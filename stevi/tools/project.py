"""Geteilte Helfer für Werkzeuge, die an bestehenden Mod-Projekten arbeiten.

Findet Projekte im Workspace, liest deren Metadaten aus ``fabric.mod.json``,
verwaltet ein kleines Inhalts-Manifest (``.stevi/content.json``) und regeneriert
daraus deterministisch die Registrierungs-Klassen (ModItems/ModBlocks). Außerdem:
sicheres Verbinden von Pfaden (kein Ausbrechen aus dem Projekt), Sprachdatei-Merge,
Platzhalter-Texturen und das Einklinken von ``initialize()``-Aufrufen.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Any

from .fabric_mod import slugify_mod_id


# ---------------------------------------------------------------------------
# Projekt finden & Metadaten lesen
# ---------------------------------------------------------------------------


def find_project(workspace: Path, identifier: str) -> Path | None:
    """Findet ein Mod-Projekt im Workspace anhand von Mod-ID, Ordnername oder Name."""
    if not workspace.is_dir():
        return None

    candidates = [workspace / identifier, workspace / slugify_mod_id(identifier)]
    for cand in candidates:
        if (cand / "src/main/resources/fabric.mod.json").is_file():
            return cand

    ident = identifier.strip().lower()
    for child in sorted(workspace.iterdir()):
        meta_file = child / "src/main/resources/fabric.mod.json"
        if not meta_file.is_file():
            continue
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if ident in (str(meta.get("id", "")).lower(), str(meta.get("name", "")).lower()):
            return child
    return None


def read_mod_meta(project: Path) -> dict[str, Any]:
    """Liest Mod-ID, Package und Hauptklasse aus fabric.mod.json."""
    meta = json.loads(
        (project / "src/main/resources/fabric.mod.json").read_text(encoding="utf-8")
    )
    main_entry = (meta.get("entrypoints", {}).get("main") or [""])[0]
    package = main_entry.rsplit(".", 1)[0] if "." in main_entry else "net.stevi.mod"
    main_class = main_entry.rsplit(".", 1)[-1] if main_entry else "Mod"
    return {
        "mod_id": meta.get("id", "mod"),
        "name": meta.get("name", "Mod"),
        "package": package,
        "main_class": main_class,
        "main_fqcn": main_entry,
    }


# ---------------------------------------------------------------------------
# Inhalts-Manifest (von Stevi gepflegt)
# ---------------------------------------------------------------------------


def _manifest_path(project: Path) -> Path:
    return project / ".stevi" / "content.json"


def load_content(project: Path) -> dict[str, list[dict[str, str]]]:
    path = _manifest_path(project)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"items": [], "blocks": []}


def save_content(project: Path, content: dict[str, list[dict[str, str]]]) -> None:
    path = _manifest_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Pfade & Dateien
# ---------------------------------------------------------------------------


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def safe_join(base: Path, relative: str) -> Path | None:
    """Verbindet base + relativen Pfad und verhindert Ausbrechen (../) aus base."""
    base = base.resolve()
    target = (base / relative).resolve()
    if base == target or base in target.parents:
        return target
    return None


def java_file(project: Path, package: str, class_name: str) -> Path:
    return project / "src/main/java" / package.replace(".", "/") / f"{class_name}.java"


def merge_lang(project: Path, mod_id: str, entries: dict[str, str]) -> None:
    """Fügt Einträge in die en_us.json ein (vorhandene bleiben erhalten)."""
    lang_path = project / f"src/main/resources/assets/{mod_id}/lang/en_us.json"
    data: dict[str, str] = {}
    if lang_path.is_file():
        try:
            data = json.loads(lang_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    data.update(entries)
    write_file(lang_path, json.dumps(dict(sorted(data.items())), indent=2, ensure_ascii=False) + "\n")


def placeholder_png(rgba: tuple[int, int, int, int] = (178, 52, 160, 255)) -> bytes:
    """Erzeugt eine gültige 16x16-PNG (einfarbig) als Platzhalter-Textur."""
    width = height = 16
    row = bytes(rgba) * width
    raw = b"".join(b"\x00" + row for _ in range(height))

    def chunk(typ: bytes, data: bytes) -> bytes:
        body = typ + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    idat = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def write_placeholder_texture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(placeholder_png())


def ensure_init_call(project: Path, meta: dict[str, Any], call: str) -> bool:
    """Fügt einen ``initialize()``-Aufruf in onInitialize() ein (idempotent).

    Gibt True zurück, wenn etwas eingefügt wurde.
    """
    main_path = java_file(project, meta["package"], meta["main_class"])
    if not main_path.is_file():
        return False
    text = main_path.read_text(encoding="utf-8")
    if call in text:
        return False
    marker = "onInitialize() {"
    idx = text.find(marker)
    if idx == -1:
        return False
    insert_at = idx + len(marker)
    new_text = text[:insert_at] + f"\n        {call}" + text[insert_at:]
    main_path.write_text(new_text, encoding="utf-8")
    return True
