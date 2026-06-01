"""Konfiguration für Stevi.

Liest Einstellungen aus Umgebungsvariablen (und optional aus einer .env-Datei).
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


# Standardmodell: das fähigste Claude-Modell. Für reinen Chat ist
# "claude-sonnet-4-6" eine günstigere Alternative.
DEFAULT_MODEL = "claude-opus-4-8"


@dataclass
class Config:
    """Gesammelte Laufzeit-Einstellungen für Stevi."""

    api_key: str | None
    model: str
    workspace: Path

    @classmethod
    def from_env(cls) -> "Config":
        """Erzeugt eine Konfiguration aus den Umgebungsvariablen."""
        workspace = Path(os.environ.get("STEVI_WORKSPACE", "./workspace")).resolve()
        return cls(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            model=os.environ.get("STEVI_MODEL", DEFAULT_MODEL),
            workspace=workspace,
        )

    def require_api_key(self) -> str:
        """Gibt den API-Schlüssel zurück oder wirft einen verständlichen Fehler."""
        if not self.api_key:
            raise RuntimeError(
                "Kein ANTHROPIC_API_KEY gefunden.\n"
                "Lege eine .env-Datei an (siehe .env.example) oder setze die "
                "Umgebungsvariable ANTHROPIC_API_KEY.\n"
                "Einen Schlüssel bekommst du auf https://console.anthropic.com"
            )
        return self.api_key
