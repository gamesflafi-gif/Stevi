"""Stevis Werkzeuge — die Dinge, die der Agent tatsächlich *tun* kann.

Dieses Modul sammelt die Tool-Definitionen (JSON-Schema für Claude) und liefert
einen Dispatcher, der einen Tool-Aufruf ausführt und ein Textergebnis zurückgibt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from . import fabric_mod, modpack

# Signatur eines Tool-Handlers: (eingabe-dict, workspace) -> ergebnis-text
Handler = Callable[[dict[str, Any], Path], str]


# Schemas, die Claude sieht. Beschreibungen sind bewusst prägnant und sagen,
# WANN das Werkzeug zu benutzen ist.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "create_fabric_mod",
        "description": (
            "Lege ein komplettes, kompilierbares Fabric-Mod-Gradle-Projekt an. "
            "Benutze dies, wenn der Nutzer eine neue Minecraft-Mod (Fabric) "
            "erstellt haben möchte. Erzeugt build.gradle, gradle.properties, "
            "fabric.mod.json, die Haupt-Mod-Klasse, Mixin-Config u.a."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Anzeigename der Mod, z.B. 'Magic Wands'.",
                },
                "mod_id": {
                    "type": "string",
                    "description": (
                        "Eindeutige Mod-ID (klein, nur a-z, 0-9, _). Wenn leer, "
                        "wird sie aus dem Namen abgeleitet, z.B. 'magic_wands'."
                    ),
                },
                "package": {
                    "type": "string",
                    "description": (
                        "Java-Package, z.B. 'com.example.magicwands'. Wenn leer, "
                        "wird 'net.stevi.<mod_id>' verwendet."
                    ),
                },
                "minecraft_version": {
                    "type": "string",
                    "description": "Ziel-Minecraft-Version, z.B. '1.21.1'.",
                },
                "description": {
                    "type": "string",
                    "description": "Kurze Beschreibung der Mod.",
                },
                "author": {
                    "type": "string",
                    "description": "Name des Autors/der Autorin (optional).",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "create_modpack",
        "description": (
            "Lege eine Modpack-Struktur mit Modrinth-Manifest (modrinth.index.json) "
            "an. Benutze dies, wenn der Nutzer ein neues Modpack starten möchte."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name des Modpacks, z.B. 'Stevis Abenteuer'.",
                },
                "minecraft_version": {
                    "type": "string",
                    "description": "Minecraft-Version, z.B. '1.21.1'.",
                },
                "loader": {
                    "type": "string",
                    "description": "Mod-Loader: 'fabric' (Standard), 'forge', 'neoforge' oder 'quilt'.",
                },
                "summary": {
                    "type": "string",
                    "description": "Kurze Beschreibung des Modpacks (optional).",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "add_mod_to_modpack",
        "description": (
            "Füge einem bestehenden Modpack einen Mod-Eintrag hinzu (Name + "
            "optional Download-URL). Benutze dies, nachdem ein Modpack angelegt wurde."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "modpack_name": {
                    "type": "string",
                    "description": "Name des Modpacks, zu dem der Mod gehört.",
                },
                "mod_name": {
                    "type": "string",
                    "description": "Name des hinzuzufügenden Mods, z.B. 'Sodium'.",
                },
                "download_url": {
                    "type": "string",
                    "description": "Direkter Download-Link zur .jar (optional).",
                },
            },
            "required": ["modpack_name", "mod_name"],
        },
    },
    {
        "name": "list_workspace",
        "description": (
            "Zeige, welche Mods und Modpacks bereits im Arbeitsverzeichnis liegen."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _list_workspace(_: dict[str, Any], workspace: Path) -> str:
    if not workspace.exists():
        return "Das Arbeitsverzeichnis ist noch leer — es wurde noch nichts erstellt."
    entries = sorted(p.name for p in workspace.iterdir() if p.is_dir())
    if not entries:
        return "Das Arbeitsverzeichnis ist noch leer — es wurde noch nichts erstellt."
    lines = [f"Inhalt von {workspace}:"]
    lines += [f"  • {name}" for name in entries]
    return "\n".join(lines)


_HANDLERS: dict[str, Handler] = {
    "create_fabric_mod": fabric_mod.create_fabric_mod,
    "create_modpack": modpack.create_modpack,
    "add_mod_to_modpack": modpack.add_mod_to_modpack,
    "list_workspace": _list_workspace,
}


def execute_tool(name: str, tool_input: dict[str, Any], workspace: Path) -> str:
    """Führt ein Werkzeug aus und gibt ein Textergebnis (oder eine Fehlermeldung) zurück."""
    handler = _HANDLERS.get(name)
    if handler is None:
        return f"Unbekanntes Werkzeug: {name}"
    try:
        return handler(tool_input, workspace)
    except Exception as exc:  # pragma: no cover - defensive
        return (
            f"Beim Ausführen von '{name}' ist ein Fehler aufgetreten: {exc}\n"
            f"Eingabe war: {json.dumps(tool_input, ensure_ascii=False)}"
        )


__all__ = ["TOOL_SCHEMAS", "execute_tool"]
