"""Austauschbare "Gehirne" (Backends) für Stevi.

Ein Backend kapselt das Gespräch mit einem Sprachmodell — entweder lokal über
Ollama (kostenlos) oder über die Anthropic-Claude-API. Der Agent spricht nur mit
dem abstrakten ``Backend``-Interface und muss nicht wissen, welches Modell dahinter
steckt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..config import Config


@dataclass
class ToolCall:
    """Ein vom Modell gewünschter Werkzeug-Aufruf."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResult:
    """Das Ergebnis eines ausgeführten Werkzeugs, das ans Modell zurückgeht."""

    tool_call_id: str
    name: str
    content: str


@dataclass
class StepResult:
    """Ergebnis eines einzelnen Modell-Schrittes."""

    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class Backend:
    """Abstrakte Basis aller Stevi-Backends."""

    name = "base"

    def reset(self) -> None:
        """Setzt die Gesprächshistorie zurück."""
        raise NotImplementedError

    def send_user(self, text: str, context: str | None = None) -> None:
        """Fügt eine Nutzernachricht (optional mit RAG-Kontext) zur Historie hinzu."""
        raise NotImplementedError

    def step(self, on_text: Callable[[str], None] | None = None) -> StepResult:
        """Führt EINEN Modell-Aufruf aus und gibt Text + gewünschte Tool-Aufrufe zurück."""
        raise NotImplementedError

    def add_tool_results(self, results: list[ToolResult]) -> None:
        """Hängt die Werkzeug-Ergebnisse an die Historie an."""
        raise NotImplementedError


def build_backend(config: Config) -> Backend:
    """Erzeugt das passende Backend laut Konfiguration."""
    if config.backend == "ollama":
        from .ollama import OllamaBackend

        return OllamaBackend(config)
    if config.backend == "claude":
        from .claude import ClaudeBackend

        return ClaudeBackend(config)
    raise ValueError(f"Unbekanntes Backend: {config.backend!r}")


__all__ = [
    "Backend",
    "ToolCall",
    "ToolResult",
    "StepResult",
    "build_backend",
]
