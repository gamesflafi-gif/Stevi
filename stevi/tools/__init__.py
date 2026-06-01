"""Stevis Werkzeuge — die Dinge, die der Agent tatsächlich *tun* kann.

Dieses Modul sammelt die Tool-Definitionen (JSON-Schema für Claude) und liefert
einen Dispatcher, der einen Tool-Aufruf ausführt und ein Textergebnis zurückgibt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from . import analyze, build, content, fabric_mod, mixin, modpack

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
    # ---- Phase 2: Inhalte zu einer Mod hinzufügen --------------------------
    {
        "name": "add_item",
        "description": (
            "Füge einer bestehenden Fabric-Mod ein neues Item hinzu (Registrierung, "
            "Modell, Sprach-Eintrag, Platzhalter-Textur). Die Mod muss bereits mit "
            "create_fabric_mod existieren."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mod": {"type": "string", "description": "Mod-ID oder Name der Ziel-Mod."},
                "name": {"type": "string", "description": "Anzeigename des Items, z.B. 'Ruby'."},
                "item_id": {
                    "type": "string",
                    "description": "Registry-ID (klein, optional; sonst aus Name abgeleitet).",
                },
            },
            "required": ["mod", "name"],
        },
    },
    {
        "name": "add_block",
        "description": (
            "Füge einer bestehenden Fabric-Mod einen neuen Block hinzu (Block + "
            "BlockItem, Blockstate, Modelle, Loot-Table, Sprach-Eintrag, Textur)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mod": {"type": "string", "description": "Mod-ID oder Name der Ziel-Mod."},
                "name": {"type": "string", "description": "Anzeigename des Blocks, z.B. 'Ruby Ore'."},
                "block_id": {
                    "type": "string",
                    "description": "Registry-ID (klein, optional; sonst aus Name abgeleitet).",
                },
            },
            "required": ["mod", "name"],
        },
    },
    # ---- Phase 3: Bauen ----------------------------------------------------
    {
        "name": "build_mod",
        "description": (
            "Baue eine Mod mit Gradle (./gradlew build). Gibt Erfolg oder die "
            "Fehlerausgabe zurück, damit du Fehler beheben kannst. Benötigt JDK + "
            "Gradle/Wrapper zur Laufzeit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mod": {"type": "string", "description": "Mod-ID oder Name der zu bauenden Mod."}
            },
            "required": ["mod"],
        },
    },
    # ---- Phase 4: Analysieren & Umschreiben --------------------------------
    {
        "name": "analyze_mod",
        "description": (
            "Analysiere eine bestehende Mod: Metadaten, registrierte Items/Blöcke, "
            "Dateiübersicht. Nutze dies, bevor du eine Mod umschreibst."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mod": {"type": "string", "description": "Mod-ID oder Name der Mod."}
            },
            "required": ["mod"],
        },
    },
    {
        "name": "read_mod_file",
        "description": (
            "Lies eine einzelne Datei eines Mod-Projekts (Pfad relativ zum "
            "Projektordner), um sie zu verstehen oder vor einer Änderung anzusehen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mod": {"type": "string", "description": "Mod-ID oder Name der Mod."},
                "path": {
                    "type": "string",
                    "description": "Relativer Pfad, z.B. 'src/main/resources/fabric.mod.json'.",
                },
            },
            "required": ["mod", "path"],
        },
    },
    {
        "name": "write_mod_file",
        "description": (
            "Schreibe/überschreibe eine Datei eines Mod-Projekts (Pfad relativ zum "
            "Projektordner). So schreibst du bestehende Mods um. Danach build_mod."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mod": {"type": "string", "description": "Mod-ID oder Name der Mod."},
                "path": {"type": "string", "description": "Relativer Pfad der Datei."},
                "content": {"type": "string", "description": "Der vollständige neue Dateiinhalt."},
            },
            "required": ["mod", "path", "content"],
        },
    },
    {
        "name": "add_mixin",
        "description": (
            "Erzeuge ein Mixin-Gerüst, um in bestehenden Minecraft-Code einzugreifen, "
            "und trage es in die mixins.json ein. Für Eingriffe ins Vanilla-Verhalten."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mod": {"type": "string", "description": "Mod-ID oder Name der Mod."},
                "target_class": {
                    "type": "string",
                    "description": "Voll qualifizierte Ziel-Klasse, z.B. 'net.minecraft.client.MinecraftClient'.",
                },
                "mixin_name": {
                    "type": "string",
                    "description": "Name der Mixin-Klasse (optional; sonst abgeleitet).",
                },
                "side": {
                    "type": "string",
                    "description": "'client' (Standard) oder 'main' (gemeinsam).",
                },
            },
            "required": ["mod", "target_class"],
        },
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
    # Phase 2
    "add_item": content.add_item,
    "add_block": content.add_block,
    # Phase 3
    "build_mod": build.build_mod,
    # Phase 4
    "analyze_mod": analyze.analyze_mod,
    "read_mod_file": analyze.read_mod_file,
    "write_mod_file": analyze.write_mod_file,
    "add_mixin": mixin.add_mixin,
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
