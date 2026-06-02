"""Phase-4-Werkzeuge: bestehende Mods analysieren und gezielt umschreiben.

- ``analyze_mod``: liest Metadaten, registrierte Items/Blöcke und eine Dateiübersicht.
- ``read_mod_file`` / ``write_mod_file``: einzelne Dateien eines Projekts lesen/ändern
  (sicher auf den Projektordner beschränkt — kein Ausbrechen via ``..``).
Mit Lesen + Schreiben + Bauen kann Stevi bestehende Mods analysieren und umschreiben.
"""

from __future__ import annotations

import json
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


def validate_mod(tool_input: dict[str, Any], workspace: Path) -> str:
    """Prüft eine Mod auf häufige Fehlerquellen, BEVOR gebaut wird.

    Findet fehlende Modelle/Texturen/Sprach-Einträge/Loot-Tables und prüft, ob die
    in der mixins.json gelisteten Mixins als Java-Datei existieren. Pure Analyse —
    ändert nichts.
    """
    project = P.find_project(workspace, tool_input["mod"].strip())
    if project is None:
        return f"Keine Mod '{tool_input['mod']}' im Workspace gefunden."

    meta = P.read_mod_meta(project)
    mod_id = meta["mod_id"]
    res = project / f"src/main/resources/assets/{mod_id}"
    data = project / f"src/main/resources/data/{mod_id}"
    problems: list[str] = []

    # Hauptklasse vorhanden?
    main = P.java_file(project, meta["package"], meta["main_class"])
    if not main.is_file():
        problems.append(f"Hauptklasse fehlt: {meta['main_fqcn']}")

    # Sprachdatei einlesen (für Lang-Checks).
    lang_path = res / "lang/en_us.json"
    lang: dict[str, str] = {}
    if lang_path.is_file():
        try:
            lang = json.loads(lang_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            problems.append("lang/en_us.json ist kein gültiges JSON.")

    content = P.load_content(project)
    for item in content.get("items", []):
        name = item["name"]
        if not (res / f"models/item/{name}.json").is_file():
            problems.append(f"Item '{name}': Modell fehlt (models/item/{name}.json).")
        if not (res / f"textures/item/{name}.png").is_file():
            problems.append(f"Item '{name}': Textur fehlt (textures/item/{name}.png).")
        if f"item.{mod_id}.{name}" not in lang:
            problems.append(f"Item '{name}': Sprach-Eintrag item.{mod_id}.{name} fehlt.")

    for block in content.get("blocks", []):
        name = block["name"]
        for rel, label in [
            (res / f"blockstates/{name}.json", "Blockstate"),
            (res / f"models/block/{name}.json", "Block-Modell"),
            (res / f"textures/block/{name}.png", "Textur"),
            (data / f"loot_table/blocks/{name}.json", "Loot-Table"),
        ]:
            if not rel.is_file():
                problems.append(f"Block '{name}': {label} fehlt.")
        if f"block.{mod_id}.{name}" not in lang:
            problems.append(f"Block '{name}': Sprach-Eintrag block.{mod_id}.{name} fehlt.")

    # Mixins: gelistete Einträge müssen als .java existieren.
    mixin_cfg = project / f"src/main/resources/{mod_id}.mixins.json"
    if mixin_cfg.is_file():
        try:
            cfg = json.loads(mixin_cfg.read_text(encoding="utf-8"))
            base = cfg.get("package", "")
            for key in ("mixins", "client"):
                for entry in cfg.get(key, []):
                    fqcn = f"{base}.{entry}"
                    pkg, cls = fqcn.rsplit(".", 1)
                    if not P.java_file(project, pkg, cls).is_file():
                        problems.append(f"Mixin '{entry}' in mixins.json hat keine Java-Datei.")
        except json.JSONDecodeError:
            problems.append(f"{mod_id}.mixins.json ist kein gültiges JSON.")

    header = f"🔎 Validierung der Mod '{meta['name']}'."
    if not problems:
        return f"{header}\n   ✅ Keine Probleme gefunden — bereit zum Bauen (build_mod)."
    return header + "\n" + "\n".join(f"   ❌ {p}" for p in problems)


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
