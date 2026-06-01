"""Werkzeug: Modpacks erzeugen und verwalten.

Erzeugt eine Modpack-Struktur mit einem Modrinth-Manifest (``modrinth.index.json``,
Format ``.mrpack``). Mods können anschließend hinzugefügt werden. Das Manifest lässt
sich mit Prism Launcher / dem Modrinth-App importieren.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

VALID_LOADERS = {"fabric", "forge", "neoforge", "quilt"}
DEFAULT_LOADER = "fabric"
DEFAULT_MC_VERSION = "1.21.1"

# Loader-Versions-Schlüssel im Modrinth-Format je Loader.
_LOADER_DEP_KEY = {
    "fabric": "fabric-loader",
    "quilt": "quilt-loader",
    "forge": "forge",
    "neoforge": "neoforge",
}


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "modpack"


def _manifest_path(workspace: Path, modpack_name: str) -> Path:
    return workspace / slugify(modpack_name) / "modrinth.index.json"


def _read_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def create_modpack(tool_input: dict[str, Any], workspace: Path) -> str:
    """Legt eine neue Modpack-Struktur mit Modrinth-Manifest an."""
    name: str = tool_input["name"].strip()
    mc_version: str = (tool_input.get("minecraft_version") or "").strip() or DEFAULT_MC_VERSION
    loader: str = (tool_input.get("loader") or DEFAULT_LOADER).strip().lower()
    summary: str = (tool_input.get("summary") or "").strip()

    if loader not in VALID_LOADERS:
        return (
            f"Unbekannter Loader '{loader}'. Erlaubt sind: "
            f"{', '.join(sorted(VALID_LOADERS))}."
        )

    slug = slugify(name)
    pack_dir = workspace / slug
    manifest_path = pack_dir / "modrinth.index.json"
    if manifest_path.exists():
        return f"Ein Modpack '{name}' existiert bereits unter {pack_dir}."

    loader_key = _LOADER_DEP_KEY[loader]
    manifest: dict[str, Any] = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": "1.0.0",
        "name": name,
        "summary": summary,
        "files": [],
        "dependencies": {
            "minecraft": mc_version,
            loader_key: "*",
        },
    }
    _write_manifest(manifest_path, manifest)

    # Übliche Modpack-Ordner für lokale Konfigs/Overrides anlegen.
    (pack_dir / "overrides" / "config").mkdir(parents=True, exist_ok=True)
    (pack_dir / "overrides" / "mods").mkdir(parents=True, exist_ok=True)
    (pack_dir / "README.md").write_text(
        _MODPACK_README.format(name=name, mc_version=mc_version, loader=loader),
        encoding="utf-8",
    )

    return (
        f"✅ Modpack '{name}' wurde angelegt unter:\n  {pack_dir}\n\n"
        f"  • Minecraft: {mc_version}\n"
        f"  • Loader:    {loader}\n"
        f"  • Manifest:  modrinth.index.json (Modrinth-Format)\n\n"
        f"Füge jetzt Mods hinzu, z.B.:  add_mod_to_modpack(modpack_name='{name}', mod_name='Sodium').\n"
        f"Eigene Configs/Mods kannst du unter 'overrides/' ablegen."
    )


def add_mod_to_modpack(tool_input: dict[str, Any], workspace: Path) -> str:
    """Fügt dem Modpack-Manifest einen Mod-Eintrag hinzu."""
    modpack_name: str = tool_input["modpack_name"].strip()
    mod_name: str = tool_input["mod_name"].strip()
    download_url: str = (tool_input.get("download_url") or "").strip()

    manifest_path = _manifest_path(workspace, modpack_name)
    if not manifest_path.exists():
        return (
            f"Kein Modpack '{modpack_name}' gefunden. Lege es zuerst mit "
            f"create_modpack an."
        )

    manifest = _read_manifest(manifest_path)
    files: list[dict[str, Any]] = manifest.setdefault("files", [])

    # Doppelte Einträge (gleicher Name) vermeiden.
    existing = {f.get("_name", "").lower() for f in files}
    if mod_name.lower() in existing:
        return f"'{mod_name}' ist bereits im Modpack '{modpack_name}' enthalten."

    slug = slugify(mod_name)
    entry: dict[str, Any] = {
        # "_name" ist ein Stevi-internes Feld, das die Lesbarkeit erhöht;
        # Launcher ignorieren unbekannte Felder.
        "_name": mod_name,
        "path": f"mods/{slug}.jar",
        "downloads": [download_url] if download_url else [],
        "env": {"client": "required", "server": "required"},
    }
    files.append(entry)
    _write_manifest(manifest_path, manifest)

    note = "" if download_url else (
        "  (Noch keine Download-URL hinterlegt — füge sie später hinzu oder lege die "
        ".jar manuell in 'overrides/mods/' ab.)\n"
    )
    return (
        f"✅ '{mod_name}' wurde zum Modpack '{modpack_name}' hinzugefügt.\n"
        f"{note}"
        f"Das Modpack enthält jetzt {len(files)} Mod(s)."
    )


_MODPACK_README = """\
# {name}

Ein Minecraft-Modpack ({loader}, Minecraft {mc_version}), erstellt mit Stevi.

## Struktur

- `modrinth.index.json` — das Manifest im Modrinth-Format (Liste aller Mods).
- `overrides/` — eigene Configs und manuell hinzugefügte Mods (`overrides/mods/`).

## Importieren / Spielen

Das Manifest lässt sich mit dem **Modrinth App** oder **Prism Launcher**
importieren. Mods mit hinterlegter Download-URL werden automatisch geladen; Mods
ohne URL legst du als `.jar` in `overrides/mods/` ab.
"""
