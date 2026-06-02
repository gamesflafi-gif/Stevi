"""Der Stevi-Agent: verbindet Backend (LLM), Wissensdatenbank und Werkzeuge.

Der Agent ist backend-unabhängig — er funktioniert gleich, egal ob ein lokales
Ollama-Modell (kostenlos) oder die Claude-API dahintersteckt. Er reichert jede
Nutzerfrage mit passendem Wissen an (RAG) und führt die agentische
Werkzeug-Schleife aus, bis Stevi fertig geantwortet hat.
"""

from __future__ import annotations

from typing import Any, Callable

from .backends import ToolResult, build_backend
from .config import Config
from .knowledge import KnowledgeBase
from .tools import execute_tool

# Sicherheitsnetz gegen Endlosschleifen bei Werkzeug-Aufrufen.
MAX_TOOL_ITERATIONS = 8


class Agent:
    """Stevi als zustandsbehafteter Chat-Agent."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.knowledge = KnowledgeBase(extra_dirs=[config.knowledge_dir])
        self.backend = build_backend(config)
        self.config.workspace.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        self.backend.reset()

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
        context = self.knowledge.context_for(user_text)
        self.backend.send_user(user_text, context or None)

        final_text_parts: list[str] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            result = self.backend.step(on_text=on_text)
            if result.text:
                final_text_parts.append(result.text)

            if not result.tool_calls:
                break

            tool_results: list[ToolResult] = []
            for call in result.tool_calls:
                if on_tool is not None:
                    on_tool(call.name, call.input)
                output = execute_tool(call.name, call.input, self.config.workspace)
                tool_results.append(
                    ToolResult(tool_call_id=call.id, name=call.name, content=output)
                )
            self.backend.add_tool_results(tool_results)
        else:
            note = (
                "\n[Hinweis: Maximale Anzahl an Werkzeug-Schritten erreicht. "
                "Frag mich, wenn ich weitermachen soll.]"
            )
            final_text_parts.append(note)
            if on_text is not None:
                on_text(note)

        return "".join(final_text_parts).strip()
