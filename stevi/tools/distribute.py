"""Phase-5-Werkzeuge: Modpacks ausliefern & Mods auflösen.

- ``add_mod_from_modrinth``: sucht/holt einen Mod über die Modrinth-API und fügt ihn
  mit echtem Download-Link, Hashes und Dateigröße ins Modpack ein (gültiger
  ``.mrpack``-Eintrag).
- ``export_modpack``: packt das Modpack in eine fertige ``.mrpack``-Datei (ZIP),
  importierbar mit Prism Launcher / Modrinth App.
- ``validate_modpack``: prüft das Manifest auf Konsistenz (Loader/Version, doppelte
  Pfade, Mods ohne Download-Quelle).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from .modpack import _LOADER_DEP_KEY, _manifest_path, _read_manifest, _write_manifest, slugify

MODRINTH_API = "https://api.modrinth.com/v2"
USER_AGENT = "Stevi-Minecraft-Modding-AI (github.com/gamesflafi-gif/Stevi)"
HTTP_TIMEOUT = 30

# Loader-Dep-Schlüssel -> Loader-Name (Umkehrung von _LOADER_DEP_KEY).
_DEP_KEY_TO_LOADER = {v: k for k, v in _LOADER_DEP_KEY.items()}


def _get_json(url: str) -> Any:
    """Holt JSON von einer URL (mit User-Agent). In Tests monkeypatchbar."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _search_project(query: str) -> tuple[str, str] | None:
    """Sucht ein Mod-Projekt auf Modrinth. Gibt (slug, titel) zurück."""
    facets = json.dumps([["project_type:mod"]])
    params = urllib.parse.urlencode({"query": query, "limit": 1, "facets": facets})
    data = _get_json(f"{MODRINTH_API}/search?{params}")
    hits = data.get("hits") or []
    if not hits:
        return None
    return hits[0].get("slug") or hits[0].get("project_id"), hits[0].get("title", query)


def _get_version(slug: str, loader: str, mc_version: str) -> dict[str, Any] | None:
    """Holt die passende neueste Mod-Version für Loader + Minecraft-Version."""
    loaders = urllib.parse.quote(json.dumps([loader]))
    games = urllib.parse.quote(json.dumps([mc_version]))
    url = f"{MODRINTH_API}/project/{slug}/version?loaders={loaders}&game_versions={games}"
    versions = _get_json(url)
    if not versions:
        return None
    return versions[0]  # API liefert neueste zuerst


def _get_version_by_id(version_id: str) -> dict[str, Any] | None:
    """Holt eine bestimmte Mod-Version anhand ihrer ID."""
    return _get_json(f"{MODRINTH_API}/version/{version_id}")


def _make_entry(version: dict[str, Any], title: str) -> dict[str, Any] | None:
    """Baut aus einer Modrinth-Version einen gültigen .mrpack-Datei-Eintrag."""
    files = version.get("files") or []
    primary = next((f for f in files if f.get("primary")), files[0] if files else None)
    if not primary:
        return None
    return {
        "_name": title,
        "path": f"mods/{primary['filename']}",
        "hashes": primary.get("hashes", {}),
        "downloads": [primary["url"]],
        "fileSize": primary.get("size", 0),
        "env": {"client": "required", "server": "required"},
    }


def _loader_from_manifest(manifest: dict[str, Any]) -> str:
    for key in manifest.get("dependencies", {}):
        if key in _DEP_KEY_TO_LOADER:
            return _DEP_KEY_TO_LOADER[key]
    return "fabric"


def add_mod_from_modrinth(tool_input: dict[str, Any], workspace: Path) -> str:
    """Löst einen Mod über Modrinth auf und fügt ihn ins Modpack ein."""
    modpack_name = tool_input["modpack_name"].strip()
    query = tool_input["mod"].strip()

    manifest_path = _manifest_path(workspace, modpack_name)
    if not manifest_path.exists():
        return f"Kein Modpack '{modpack_name}' gefunden. Lege es zuerst mit create_modpack an."
    manifest = _read_manifest(manifest_path)

    mc_version = (tool_input.get("minecraft_version") or "").strip() or manifest.get(
        "dependencies", {}
    ).get("minecraft", "")
    loader = (tool_input.get("loader") or "").strip().lower() or _loader_from_manifest(manifest)
    if not mc_version:
        return "Im Modpack ist keine Minecraft-Version hinterlegt — bitte angeben."

    try:
        found = _search_project(query)
        if not found:
            return f"Auf Modrinth wurde kein Mod zu '{query}' gefunden."
        slug, title = found
        version = _get_version(slug, loader, mc_version)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        return (
            f"Konnte Modrinth nicht erreichen ({exc}). Prüfe deine Internetverbindung "
            f"oder füge den Mod mit add_mod_to_modpack manuell hinzu."
        )

    if not version:
        return (
            f"'{title}' hat keine Version für {loader} {mc_version}. Versuche eine "
            f"andere Minecraft-Version oder einen anderen Loader."
        )

    main_entry = _make_entry(version, title)
    if not main_entry:
        return f"Die gefundene Version von '{title}' enthält keine Datei."

    # Optional: benötigte Abhängigkeiten gleich mit auflösen.
    with_deps = tool_input.get("with_dependencies", True)
    if isinstance(with_deps, str):
        with_deps = with_deps.strip().lower() not in ("false", "0", "nein", "no")

    queue: list[dict[str, Any]] = [main_entry]
    if with_deps:
        for dep in version.get("dependencies") or []:
            if dep.get("dependency_type") != "required":
                continue
            try:
                if dep.get("version_id"):
                    dep_version = _get_version_by_id(dep["version_id"])
                elif dep.get("project_id"):
                    dep_version = _get_version(dep["project_id"], loader, mc_version)
                else:
                    dep_version = None
            except (urllib.error.URLError, json.JSONDecodeError):
                dep_version = None
            if not dep_version:
                continue
            dep_title = (dep.get("file_name") or "").removesuffix(".jar") or dep.get(
                "project_id", "Abhängigkeit"
            )
            dep_entry = _make_entry(dep_version, dep_title)
            if dep_entry:
                queue.append(dep_entry)

    pack_files: list[dict[str, Any]] = manifest.setdefault("files", [])
    existing = {f.get("path") for f in pack_files}
    added: list[str] = []
    for entry in queue:
        if entry["path"] in existing:
            continue
        pack_files.append(entry)
        existing.add(entry["path"])
        added.append(entry["_name"])

    if not added:
        return f"'{title}' ist (inkl. Abhängigkeiten) bereits im Modpack enthalten."
    _write_manifest(manifest_path, manifest)

    dep_note = ""
    if len(added) > 1:
        dep_note = "\n   • Mit aufgelöst: " + ", ".join(added[1:])
    return (
        f"✅ '{added[0]}' von Modrinth hinzugefügt (Version: {version.get('version_number', '?')})."
        f"{dep_note}\n"
        f"   Das Modpack enthält jetzt {len(pack_files)} Mod(s)."
    )


def search_modrinth(tool_input: dict[str, Any], workspace: Path) -> str:
    """Sucht Mods auf Modrinth und listet die besten Treffer auf."""
    query = tool_input["query"].strip()
    try:
        limit = int(tool_input.get("limit", 5) or 5)
    except (TypeError, ValueError):
        limit = 5
    limit = max(1, min(limit, 10))

    facets = json.dumps([["project_type:mod"]])
    params = urllib.parse.urlencode({"query": query, "limit": limit, "facets": facets})
    try:
        data = _get_json(f"{MODRINTH_API}/search?{params}")
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        return f"Konnte Modrinth nicht erreichen ({exc})."

    hits = data.get("hits") or []
    if not hits:
        return f"Auf Modrinth wurde nichts zu '{query}' gefunden."

    lines = [f"🔍 Top-Treffer auf Modrinth für '{query}':"]
    for h in hits:
        desc = (h.get("description") or "").strip().replace("\n", " ")
        if len(desc) > 90:
            desc = desc[:90] + "…"
        lines.append(
            f"  • {h.get('title', '?')} (slug: {h.get('slug', '?')}) — "
            f"{h.get('downloads', 0):,} Downloads\n    {desc}"
        )
    lines.append(
        "Hinzufügen mit: add_mod_from_modrinth(modpack_name=…, mod='<slug>')."
    )
    return "\n".join(lines)


def export_modpack(tool_input: dict[str, Any], workspace: Path) -> str:
    """Packt das Modpack in eine fertige .mrpack-Datei (ZIP)."""
    name = tool_input["name"].strip()
    slug = slugify(name)
    pack_dir = workspace / slug
    manifest_path = pack_dir / "modrinth.index.json"
    if not manifest_path.exists():
        return f"Kein Modpack '{name}' gefunden."

    manifest = _read_manifest(manifest_path)
    all_files = manifest.get("files", [])
    # Für den .mrpack-Index nur Dateien mit Download-Quelle; internes "_name" entfernen.
    index_files = []
    without_download = []
    for f in all_files:
        if f.get("downloads"):
            clean = {k: v for k, v in f.items() if not k.startswith("_")}
            index_files.append(clean)
        else:
            without_download.append(f.get("_name") or f.get("path", "?"))

    index = {k: v for k, v in manifest.items() if k != "files"}
    index["files"] = index_files

    out_path = workspace / f"{slug}.mrpack"
    overrides_dir = pack_dir / "overrides"
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("modrinth.index.json", json.dumps(index, indent=2, ensure_ascii=False))
        if overrides_dir.is_dir():
            for path in sorted(overrides_dir.rglob("*")):
                if path.is_file():
                    arcname = "overrides/" + str(path.relative_to(overrides_dir)).replace("\\", "/")
                    zf.write(path, arcname)

    note = ""
    if without_download:
        note = (
            f"\n   ⚠️ {len(without_download)} Mod(s) ohne Download-Quelle wurden NICHT in "
            f"den Index aufgenommen: {', '.join(without_download)}.\n"
            f"      Lege deren .jar manuell in overrides/mods/ ab oder löse sie mit "
            f"add_mod_from_modrinth auf."
        )
    return (
        f"✅ Modpack '{name}' exportiert nach:\n   {out_path}\n"
        f"   • {len(index_files)} Mod(s) im Index\n"
        f"   Importierbar mit Prism Launcher oder der Modrinth App.{note}"
    )


def validate_modpack(tool_input: dict[str, Any], workspace: Path) -> str:
    """Prüft das Modpack-Manifest auf häufige Probleme."""
    name = tool_input["name"].strip()
    manifest_path = _manifest_path(workspace, name)
    if not manifest_path.exists():
        return f"Kein Modpack '{name}' gefunden."

    manifest = _read_manifest(manifest_path)
    problems: list[str] = []
    notes: list[str] = []

    deps = manifest.get("dependencies", {})
    if not deps.get("minecraft"):
        problems.append("Keine Minecraft-Version in dependencies.")
    if not any(k in _DEP_KEY_TO_LOADER for k in deps):
        problems.append("Kein Mod-Loader (fabric/forge/neoforge/quilt) in dependencies.")

    files = manifest.get("files", [])
    paths = [f.get("path") for f in files]
    dupes = {p for p in paths if paths.count(p) > 1}
    if dupes:
        problems.append(f"Doppelte Pfade: {', '.join(sorted(dupes))}")

    no_dl = [f.get("_name") or f.get("path") for f in files if not f.get("downloads")]
    if no_dl:
        notes.append(
            f"{len(no_dl)} Mod(s) ohne Download-Quelle (brauchen eine .jar in "
            f"overrides/mods/ oder add_mod_from_modrinth): {', '.join(no_dl)}"
        )

    header = f"🔎 Validierung von Modpack '{name}' — {len(files)} Mod(s)."
    if not problems and not notes:
        return f"{header}\n   ✅ Keine Probleme gefunden."
    lines = [header]
    lines += [f"   ❌ {p}" for p in problems]
    lines += [f"   ⚠️ {n}" for n in notes]
    if not problems:
        lines.append("   ✅ Keine kritischen Fehler — nur Hinweise.")
    return "\n".join(lines)
