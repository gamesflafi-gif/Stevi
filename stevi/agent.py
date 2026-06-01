"""Der Stevi-Agent: verbindet LLM, Wissensdatenbank und Werkzeuge.

Hält die Gesprächshistorie, reichert jede Nutzerfrage mit passendem Wissen aus der
Wissensdatenbank an (RAG) und führt die agentische Werkzeug-Schleife aus, bis Stevi
fertig geantwortet hat.
"""

from __future__ import annotations

from typing import Any, Callable

from .config import Config
from .knowledge import KnowledgeBase
from .llm import LLM
from .tools import TOOL_SCHEMAS, execute_tool

# Wie oft Werkzeuge in einer einzigen Antwortrunde maximal aufgerufen werden dürfen
# (Sicherheitsnetz gegen Endlosschleifen).
MAX_TOOL_ITERATIONS = 8


class Agent:
    """Stevi als zustandsbehafteter Chat-Agent."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.llm = LLM(api_key=config.require_api_key(), model=config.model)
        self.knowledge = KnowledgeBase()
        self.messages: list[dict[str, Any]] = []
        self.config.workspace.mkdir(parents=True, exist_ok=True)

    def _build_user_message(self, user_text: str) -> dict[str, Any]:
        """Baut die Nutzer-Nachricht — bei Bedarf mit RAG-Kontext davor."""
        content: list[dict[str, Any]] = []
        context = self.knowledge.context_for(user_text)
        if context:
            content.append(
                {
                    "type": "text",
                    "text": (
                        "RELEVANTES WISSEN (aus Stevis Wissensdatenbank, nutze es "
                        "wenn passend):\n\n" + context
                    ),
                }
            )
        content.append({"type": "text", "text": user_text})
        return {"role": "user", "content": content}

    def send(
        self,
        user_text: str,
        on_text: Callable[[str], None] | None = None,
        on_tool: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> str:
        """Verarbeitet eine Nutzereingabe und gibt Stevis vollständige Textantwort zurück.

        ``on_text`` streamt Text-Deltas live. ``on_tool`` wird vor jeder
        Werkzeug-Ausführung mit (name, eingabe) aufgerufen.
        """
        self.messages.append(self._build_user_message(user_text))

        final_text_parts: list[str] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            message = self.llm.stream_turn(
                messages=self.messages,
                tools=TOOL_SCHEMAS,
                on_text=on_text,
            )
            # Vollständigen Inhalt (inkl. Thinking-Blöcke) zur Historie hinzufügen.
            self.messages.append({"role": "assistant", "content": message.content})

            # Textanteile dieser Runde sammeln.
            for block in message.content:
                if block.type == "text":
                    final_text_parts.append(block.text)

            if message.stop_reason != "tool_use":
                break

            # Alle Tool-Aufrufe dieser Runde ausführen und Ergebnisse zurückgeben.
            tool_results: list[dict[str, Any]] = []
            for block in message.content:
                if block.type == "tool_use":
                    if on_tool is not None:
                        on_tool(block.name, block.input)
                    result = execute_tool(
                        block.name, block.input, self.config.workspace
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            self.messages.append({"role": "user", "content": tool_results})
        else:
            # Schleife ohne break beendet → Iterationslimit erreicht.
            note = (
                "\n[Hinweis: Maximale Anzahl an Werkzeug-Schritten erreicht. "
                "Frag mich, wenn ich weitermachen soll.]"
            )
            final_text_parts.append(note)
            if on_text is not None:
                on_text(note)

        return "".join(final_text_parts).strip()
