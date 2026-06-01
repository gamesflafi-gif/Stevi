"""Konfiguration für Stevi.

Liest Einstellungen aus Umgebungsvariablen (und optional aus einer .env-Datei).

Stevi kann zwei "Gehirne" nutzen:
- ``ollama``  → ein lokales/selbst-gehostetes Open-Source-Modell. KOSTENLOS, ohne API.
- ``claude``  → die Anthropic-API (stärker, aber kostenpflichtig).
Mit ``STEVI_BACKEND`` wählst du, welches. Ohne Angabe entscheidet Stevi automatisch:
gibt es einen ANTHROPIC_API_KEY → claude, sonst → ollama.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv ist optional zur Laufzeit
    pass


# Standardmodell für das Claude-Backend.
DEFAULT_CLAUDE_MODEL = "claude-opus-4-8"

# Standard für das lokale Ollama-Backend. Ein gutes, schlankes Code-Modell.
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


@dataclass
class Config:
    """Gesammelte Laufzeit-Einstellungen für Stevi."""

    backend: str               # "ollama" oder "claude"
    api_key: str | None        # Anthropic-Schlüssel (nur für claude)
    claude_model: str
    ollama_host: str
    ollama_model: str
    workspace: Path

    @classmethod
    def from_env(cls) -> "Config":
        """Erzeugt eine Konfiguration aus den Umgebungsvariablen."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        backend = os.environ.get("STEVI_BACKEND", "").strip().lower()
        if backend not in ("ollama", "claude"):
            # Automatik: Schlüssel vorhanden → claude, sonst kostenlos lokal.
            backend = "claude" if api_key else "ollama"

        workspace = Path(os.environ.get("STEVI_WORKSPACE", "./workspace")).resolve()
        return cls(
            backend=backend,
            api_key=api_key,
            claude_model=os.environ.get("STEVI_MODEL", DEFAULT_CLAUDE_MODEL),
            ollama_host=os.environ.get("STEVI_OLLAMA_HOST", DEFAULT_OLLAMA_HOST),
            ollama_model=os.environ.get("STEVI_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            workspace=workspace,
        )

    @property
    def model_label(self) -> str:
        """Menschlich lesbarer Name des aktiven Modells (für Anzeigen)."""
        if self.backend == "ollama":
            return f"{self.ollama_model} (lokal/Ollama)"
        return f"{self.claude_model} (Anthropic-API)"

    def require_api_key(self) -> str:
        """Gibt den API-Schlüssel zurück oder wirft einen verständlichen Fehler."""
        if not self.api_key:
            raise RuntimeError(
                "Kein ANTHROPIC_API_KEY gefunden.\n"
                "Lege eine .env-Datei an (siehe .env.example) oder setze die "
                "Umgebungsvariable ANTHROPIC_API_KEY.\n"
                "Einen Schlüssel bekommst du auf https://console.anthropic.com\n"
                "Tipp: Für den KOSTENLOSEN Betrieb setze stattdessen "
                "STEVI_BACKEND=ollama und installiere Ollama (https://ollama.com)."
            )
        return self.api_key
