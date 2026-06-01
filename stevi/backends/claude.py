"""Claude-Backend (Anthropic-API) — stark, aber kostenpflichtig.

Nutzt Prompt-Caching auf dem System-Prompt, adaptives Denken und Streaming.
``anthropic`` wird nur hier (lazy) importiert, damit Ollama-Nutzer das Paket nicht
brauchen.
"""

from __future__ import annotations

from typing import Any, Callable

from ..config import Config
from ..prompts import SYSTEM_PROMPT
from ..tools import TOOL_SCHEMAS
from . import Backend, StepResult, ToolCall, ToolResult

MAX_TOKENS = 8000


class ClaudeBackend(Backend):
    name = "claude"

    def __init__(self, config: Config) -> None:
        import anthropic  # lazy: nur nötig, wenn Claude wirklich verwendet wird

        self.config = config
        self.model = config.claude_model
        self.client = anthropic.Anthropic(api_key=config.require_api_key())
        self.messages: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.messages.clear()

    def _system_blocks(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def send_user(self, text: str, context: str | None = None) -> None:
        content: list[dict[str, Any]] = []
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
        content.append({"type": "text", "text": text})
        self.messages.append({"role": "user", "content": content})

    def step(self, on_text: Callable[[str], None] | None = None) -> StepResult:
        with self.client.messages.stream(
            model=self.model,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=self._system_blocks(),
            tools=TOOL_SCHEMAS,
            messages=self.messages,
        ) as stream:
            if on_text is not None:
                for event in stream:
                    if (
                        event.type == "content_block_delta"
                        and event.delta.type == "text_delta"
                    ):
                        on_text(event.delta.text)
            message = stream.get_final_message()

        # Vollständigen Inhalt (inkl. Thinking-Blöcke) zur Historie hinzufügen.
        self.messages.append({"role": "assistant", "content": message.content})

        result = StepResult()
        for block in message.content:
            if block.type == "text":
                result.text += block.text
            elif block.type == "tool_use":
                result.tool_calls.append(
                    ToolCall(id=block.id, name=block.name, input=dict(block.input))
                )
        return result

    def add_tool_results(self, results: list[ToolResult]) -> None:
        self.messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": r.tool_call_id,
                        "content": r.content,
                    }
                    for r in results
                ],
            }
        )
