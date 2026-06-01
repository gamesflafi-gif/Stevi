"""Ollama-Backend — ein lokales/selbst-gehostetes Open-Source-Modell. KOSTENLOS.

Spricht über HTTP mit einem laufenden Ollama-Server (Standard: localhost:11434).
Benötigt KEINE externen API-Schlüssel und KEINE Extra-Python-Pakete (nur die
Standardbibliothek). So läuft Stevi dauerhaft kostenlos auf deinem eigenen Server.

Voraussetzung: Ollama installiert (https://ollama.com) und ein Modell gezogen, z.B.:
    ollama pull qwen2.5-coder:7b

Hinweis zu Werkzeugen: Werkzeug-Aufrufe (Tools) funktionieren nur mit Modellen, die
"tools" unterstützen (z.B. qwen2.5-coder, llama3.1, mistral-nemo). Bei kleineren
Modellen kann Stevi trotzdem chatten, ruft aber evtl. seltener Werkzeuge auf.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable

from ..config import Config
from ..prompts import SYSTEM_PROMPT
from ..tools import TOOL_SCHEMAS
from . import Backend, StepResult, ToolCall, ToolResult

# Zeitlimit pro Anfrage (Sekunden). Lokale Modelle können langsam sein.
REQUEST_TIMEOUT = 600


def _to_ollama_tools(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Wandelt Claude-Tool-Schemas in das OpenAI/Ollama-"function"-Format um."""
    tools: list[dict[str, Any]] = []
    for s in schemas:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": s["name"],
                    "description": s.get("description", ""),
                    "parameters": s.get(
                        "input_schema", {"type": "object", "properties": {}}
                    ),
                },
            }
        )
    return tools


class OllamaBackend(Backend):
    name = "ollama"

    def __init__(self, config: Config) -> None:
        self.config = config
        self.model = config.ollama_model
        self.host = config.ollama_host.rstrip("/")
        self.tools = _to_ollama_tools(TOOL_SCHEMAS)
        self.messages: list[dict[str, Any]] = []
        self.reset()

    def reset(self) -> None:
        # System-Prompt als erste Nachricht (Ollama/OpenAI-Stil).
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def send_user(self, text: str, context: str | None = None) -> None:
        if context:
            text = (
                "RELEVANTES WISSEN (aus Stevis Wissensdatenbank, nutze es wenn "
                "passend):\n\n" + context + "\n\n---\n\nFrage: " + text
            )
        self.messages.append({"role": "user", "content": text})

    def _chat(self) -> dict[str, Any]:
        """Ruft Ollamas /api/chat auf (nicht-streamend) und gibt die Antwort zurück."""
        payload = {
            "model": self.model,
            "messages": self.messages,
            "tools": self.tools,
            "stream": False,
            "options": {"temperature": 0.4},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Konnte Ollama unter {self.host} nicht erreichen ({exc}).\n"
                f"Läuft Ollama? Starte es mit 'ollama serve' und ziehe ein Modell, "
                f"z.B. 'ollama pull {self.model}'."
            ) from exc

    def step(self, on_text: Callable[[str], None] | None = None) -> StepResult:
        response = self._chat()
        message = response.get("message", {}) or {}
        content = message.get("content", "") or ""
        raw_tool_calls = message.get("tool_calls") or []

        # Assistenten-Nachricht (inkl. evtl. Tool-Aufrufe) zur Historie hinzufügen.
        self.messages.append(message)

        if content and on_text is not None:
            on_text(content)

        result = StepResult(text=content)
        for call in raw_tool_calls:
            fn = call.get("function", {}) or {}
            args = fn.get("arguments", {}) or {}
            if isinstance(args, str):
                # Manche Modelle liefern Argumente als JSON-String.
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            result.tool_calls.append(
                ToolCall(id=str(uuid.uuid4()), name=fn.get("name", ""), input=args)
            )
        return result

    def add_tool_results(self, results: list[ToolResult]) -> None:
        for r in results:
            self.messages.append(
                {"role": "tool", "tool_name": r.name, "content": r.content}
            )
