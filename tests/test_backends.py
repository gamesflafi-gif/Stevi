"""Tests für die austauschbaren Backends — ohne Netzwerk/API."""

from __future__ import annotations

from pathlib import Path

from stevi.backends import build_backend
from stevi.backends.ollama import OllamaBackend, _to_ollama_tools
from stevi.config import Config
from stevi.tools import TOOL_SCHEMAS


def _config(backend: str, api_key: str | None = None) -> Config:
    return Config(
        backend=backend,
        api_key=api_key,
        claude_model="claude-opus-4-8",
        ollama_host="http://localhost:11434",
        ollama_model="qwen2.5-coder:7b",
        workspace=Path("./workspace"),
        knowledge_dir=Path("./knowledge_data"),
    )


def test_tool_schema_conversion_to_ollama():
    tools = _to_ollama_tools(TOOL_SCHEMAS)
    assert len(tools) == len(TOOL_SCHEMAS)
    first = tools[0]
    assert first["type"] == "function"
    assert "name" in first["function"]
    assert "parameters" in first["function"]
    # Werkzeugnamen bleiben erhalten.
    names = {t["function"]["name"] for t in tools}
    assert "create_fabric_mod" in names
    assert "create_modpack" in names


def test_build_backend_selects_ollama():
    backend = build_backend(_config("ollama"))
    assert isinstance(backend, OllamaBackend)
    assert backend.name == "ollama"


def test_ollama_backend_history_and_messages():
    backend = OllamaBackend(_config("ollama"))
    # Nach reset() steht der System-Prompt als erste Nachricht.
    assert backend.messages[0]["role"] == "system"

    backend.send_user("Wie erstelle ich ein Item?", context="WISSEN: Items kommen in Registries.")
    last = backend.messages[-1]
    assert last["role"] == "user"
    assert "WISSEN" in last["content"]
    assert "Wie erstelle ich ein Item?" in last["content"]


def test_config_autodetect_backend():
    # Ohne Schlüssel und ohne STEVI_BACKEND → ollama (kostenlos).
    import os

    saved = {k: os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "STEVI_BACKEND")}
    try:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("STEVI_BACKEND", None)
        cfg = Config.from_env()
        assert cfg.backend == "ollama"

        os.environ["ANTHROPIC_API_KEY"] = "sk-test"
        cfg2 = Config.from_env()
        assert cfg2.backend == "claude"

        os.environ["STEVI_BACKEND"] = "ollama"
        cfg3 = Config.from_env()
        assert cfg3.backend == "ollama"  # explizite Wahl schlägt Automatik
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
