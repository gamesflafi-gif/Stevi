"""Dünner Wrapper um den Anthropic-Client.

Kapselt das Erstellen von Nachrichten mit:
- Prompt-Caching auf dem (stabilen) System-Prompt → spart Kosten/Zeit,
- adaptivem Denken (`thinking: adaptive`) + Effort,
- Streaming, damit Stevis Antwort live im Terminal erscheint.
"""

from __future__ import annotations

from typing import Any, Callable

import anthropic

from .prompts import SYSTEM_PROMPT

# Maximal pro Antwort erzeugte Tokens. Beim Streaming unkritisch.
MAX_TOKENS = 8000


class LLM:
    """Verbindung zu Claude für Stevi."""

    def __init__(self, api_key: str, model: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _system_blocks(self) -> list[dict[str, Any]]:
        # Der System-Prompt ist stabil → wir markieren ihn fürs Prompt-Caching.
        return [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def stream_turn(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        on_text: Callable[[str], None] | None = None,
    ) -> anthropic.types.Message:
        """Führt EINEN Modell-Aufruf aus (streamend) und gibt die finale Message zurück.

        ``on_text`` erhält Text-Deltas in Echtzeit (z.B. zum Ausgeben im Terminal).
        Tool-Aufrufe werden NICHT hier ausgeführt — das macht der Agent in seiner
        Schleife anhand der zurückgegebenen Message.
        """
        with self.client.messages.stream(
            model=self.model,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=self._system_blocks(),
            tools=tools,
            messages=messages,
        ) as stream:
            if on_text is not None:
                for event in stream:
                    if (
                        event.type == "content_block_delta"
                        and event.delta.type == "text_delta"
                    ):
                        on_text(event.delta.text)
            return stream.get_final_message()
