"""Phase-4-Werkzeuge: bestehende Mods analysieren und gezielt umschreiben.

- ``analyze_mod``: liest Metadaten, registrierte Items/Blöcke und eine Dateiübersicht.
- ``read_mod_file`` / ``write_mod_file``: einzelne Dateien eines Projekts lesen/ändern
  (sicher auf den Projektordner beschränkt — kein Ausbrechen via ``..``).
Mit Lesen + Schreiben + Bauen kann Stevi bestehende Mods analysieren und umschreiben.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import project as P

MAX_READ_CHARS = 16000


def analyze_mod(tool_input: dict[str, Any], workspace: Path) -> str:
    project = P.find_project(workspace, tool_input["mod"].strip())
    if project is None:
        return f"Keine Mod '{tool_input['mod']}' im Workspace gefunden."

    meta = P.read_mod_meta(project)
    content = P.load_content(project)

    # Java-Dateien zählen + Registrierungen grob erfassen.
    java_files = [p for p in project.rglob("*.java") if "build" not in p.parts]
    registrations: list[str] = []
    for jf in java_files:
        try:
            text = jf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(r'Identifier\.of\([^,]+,\s*"([^"]+)"\)', text):
            registrations.append(m.group(1))

    items = ", ".join(i["name"] for i in content["items"]) or "—"
    blocks = ", ".join(b["name"] for b in content["blocks"]) or "—"
    regs = ", ".join(sorted(set(registrations))) or "—"

    # Wichtige Dateien auflisten (relativ).
    key_files = []
    for rel in [
        f"src/main/java/{meta['package'].replace('.', '/')}/{meta['main_class']}.java",
        "src/main/resources/fabric.mod.json",
        "gradle.properties",
        "build.gradle",
    ]:
        if (project / rel).is_file():
            key_files.append(rel)

    return (
        f"📦 Analyse von '{meta['name']}' (id: {meta['mod_id']})\n"
        f"   Package:        {meta['package']}\n"
        f"   Hauptklasse:    {meta['main_class']}\n"
        f"   Java-Dateien:   {len(java_files)}\n"
        f"   Items (Stevi):  {items}\n"
        f"   Blöcke (Stevi): {blocks}\n"
        f"   Registrierte IDs (gefunden): {regs}\n"
        f"   Wichtige Dateien:\n"
        + "\n".join(f"     • {f}" for f in key_files)
        + "\n   Tipp: read_mod_file zum Ansehen, write_mod_file zum Ändern einer Datei."
    )


def read_mod_file(tool_input: dict[str, Any], workspace: Path) -> str:
    project = P.find_project(workspace, tool_input["mod"].strip())
    if project is None:
        return f"Keine Mod '{tool_input['mod']}' im Workspace gefunden."
    target = P.safe_join(project, tool_input["path"].strip())
    if target is None:
        return "Ungültiger Pfad (außerhalb des Projekts ist nicht erlaubt)."
    if not target.is_file():
        return f"Datei nicht gefunden: {tool_input['path']}"
    try:
        text = target.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return f"Konnte Datei nicht lesen: {exc}"
    truncated = "" if len(text) <= MAX_READ_CHARS else "\n…(gekürzt)…"
    return f"--- {tool_input['path']} ---\n{text[:MAX_READ_CHARS]}{truncated}"


def write_mod_file(tool_input: dict[str, Any], workspace: Path) -> str:
    project = P.find_project(workspace, tool_input["mod"].strip())
    if project is None:
        return f"Keine Mod '{tool_input['mod']}' im Workspace gefunden."
    target = P.safe_join(project, tool_input["path"].strip())
    if target is None:
        return "Ungültiger Pfad (außerhalb des Projekts ist nicht erlaubt)."
    content = tool_input.get("content", "")
    try:
        P.write_file(target, content)
    except OSError as exc:
        return f"Konnte Datei nicht schreiben: {exc}"
    return (
        f"✅ Datei geschrieben: {tool_input['path']} ({len(content)} Zeichen).\n"
        f"   Tipp: build_mod ausführen, um zu prüfen, ob alles kompiliert."
    )
