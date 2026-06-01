"""Wissens-Importer für Stevi (Phase 2).

Macht Stevi schlauer — ohne Training und ohne Kosten — indem echtes Material als
Text in die Wissensdatenbank aufgenommen wird:

- **Mod-Quellcode** (lokaler Ordner oder GitHub-URL): die aussagekräftigen Dateien
  (.java/.json/.kt) werden gesammelt und als durchsuchbares Markdown abgelegt.
- **Video-Transkripte** (.srt/.vtt/.txt): Untertitel werden von Zeitstempeln und
  Tags befreit und als Text gespeichert. So lernt Stevi aus Tutorials, ohne die
  Videos pixelweise „anschauen" zu müssen (das wäre teuer und schlechter).

Alles landet in ``config.knowledge_dir`` (Standard: ./knowledge_data) und wird beim
nächsten Start automatisch von der KnowledgeBase mitgeladen.

Aufruf über die CLI:
    python -m stevi import mod <ordner-oder-git-url> [Name]
    python -m stevi import transcript <datei.srt|.vtt|.txt> [Titel]
    python -m stevi import list
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import Config

# Welche Quelldateien als Wissen aufgenommen werden.
CODE_EXTENSIONS = {".java", ".kt", ".json"}
SKIP_DIRS = {
    ".git", "build", ".gradle", "out", "node_modules", ".idea", "run",
    ".fabric", "bin", ".github",
}
MAX_FILES = 60               # höchstens so viele Dateien pro Import
MAX_FILE_CHARS = 6000        # pro Datei kürzen (RAG bleibt durchsuchbar)
MAX_TOTAL_CHARS = 300_000    # Gesamt-Obergrenze pro Import
MAX_FILE_BYTES = 200_000     # einzelne Riesendateien überspringen


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "import"


def _ensure_dir(knowledge_dir: Path) -> None:
    knowledge_dir.mkdir(parents=True, exist_ok=True)


def _is_git_url(source: str) -> bool:
    return source.startswith(("http://", "https://", "git@")) or source.endswith(".git")


def _clone_repo(url: str, dest: Path) -> None:
    if shutil.which("git") is None:
        raise RuntimeError(
            "git ist nicht installiert. Installiere git oder lade die Mod-Quellen "
            "manuell herunter und gib den lokalen Ordner an."
        )
    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        check=True,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Mod-Quellcode importieren
# ---------------------------------------------------------------------------


def import_mod_source(
    source: str, knowledge_dir: Path, name: str | None = None
) -> str:
    """Importiert Mod-Quellcode (lokaler Ordner oder Git-URL) als Wissen."""
    _ensure_dir(knowledge_dir)

    tmp_dir: tempfile.TemporaryDirectory | None = None
    if _is_git_url(source):
        tmp_dir = tempfile.TemporaryDirectory(prefix="stevi-clone-")
        repo_path = Path(tmp_dir.name) / "repo"
        try:
            _clone_repo(source, repo_path)
        except subprocess.CalledProcessError as exc:
            tmp_dir.cleanup()
            return f"Konnte das Repository nicht klonen: {exc.stderr or exc}"
        root = repo_path
        default_name = source.rstrip("/").split("/")[-1].removesuffix(".git")
    else:
        root = Path(source).expanduser().resolve()
        if not root.is_dir():
            return f"Ordner nicht gefunden: {root}"
        default_name = root.name

    mod_name = name or default_name

    try:
        files = _collect_source_files(root)
    finally:
        pass  # tmp_dir wird unten freigegeben

    if not files:
        if tmp_dir:
            tmp_dir.cleanup()
        return (
            f"Keine passenden Quelldateien (.java/.kt/.json) in '{source}' gefunden."
        )

    parts: list[str] = [
        f"# Importierte Mod: {mod_name}",
        f"Quelle: {source}",
        "Dieses Wissen wurde aus echtem Mod-Quellcode importiert und dient Stevi "
        "als Referenz für Aufbau, Registrierungen und Muster.",
        "",
    ]
    total = 0
    used = 0
    for rel, content in files:
        if used >= MAX_FILES or total >= MAX_TOTAL_CHARS:
            break
        snippet = content[:MAX_FILE_CHARS]
        parts.append(f"## {rel}")
        parts.append("```")
        parts.append(snippet)
        parts.append("```")
        parts.append("")
        total += len(snippet)
        used += 1

    out_path = knowledge_dir / f"imported-mod-{slugify(mod_name)}.md"
    out_path.write_text("\n".join(parts), encoding="utf-8")

    if tmp_dir:
        tmp_dir.cleanup()

    return (
        f"✅ Mod '{mod_name}' importiert: {used} Datei(en) als Wissen gespeichert.\n"
        f"   Datei: {out_path}\n"
        f"   Stevi nutzt dieses Wissen ab dem nächsten Start automatisch."
    )


def _collect_source_files(root: Path) -> list[tuple[str, str]]:
    """Sammelt relevante Quelldateien als (relativer-pfad, inhalt)."""
    results: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not content.strip():
            continue
        results.append((str(path.relative_to(root)), content))
        if len(results) >= MAX_FILES:
            break
    return results


# ---------------------------------------------------------------------------
# Video-Transkripte importieren
# ---------------------------------------------------------------------------

_TIMESTAMP = re.compile(r"-->")
_INDEX_ONLY = re.compile(r"^\d+$")
_TAG = re.compile(r"<[^>]+>")
_VTT_TS = re.compile(r"^\d{2}:\d{2}")


def clean_transcript(text: str) -> str:
    """Entfernt Zeitstempel, Indizes und Tags aus .srt/.vtt-Untertiteln."""
    lines_out: list[str] = []
    prev = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in ("WEBVTT",) or line.startswith("NOTE"):
            continue
        if _TIMESTAMP.search(line) or _INDEX_ONLY.match(line) or _VTT_TS.match(line):
            continue
        line = _TAG.sub("", line).strip()
        if not line:
            continue
        # Aufeinanderfolgende Duplikate (typisch bei Auto-Untertiteln) zusammenfassen.
        if line == prev:
            continue
        lines_out.append(line)
        prev = line
    return "\n".join(lines_out)


def import_transcript(
    source: str, knowledge_dir: Path, title: str | None = None
) -> str:
    """Importiert ein Transkript (.srt/.vtt/.txt) als Wissen."""
    _ensure_dir(knowledge_dir)
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        return f"Datei nicht gefunden: {path}"

    raw = path.read_text(encoding="utf-8", errors="ignore")
    cleaned = clean_transcript(raw)
    if not cleaned.strip():
        return f"Im Transkript '{path.name}' wurde kein Text gefunden."

    video_title = title or path.stem
    body = (
        f"# Video-Transkript: {video_title}\n"
        f"Quelle: {path.name}\n"
        "Dieses Wissen stammt aus einem Modding-Video (Untertitel als Text).\n\n"
        f"{cleaned}\n"
    )
    out_path = knowledge_dir / f"transcript-{slugify(video_title)}.md"
    out_path.write_text(body, encoding="utf-8")

    words = len(cleaned.split())
    return (
        f"✅ Transkript '{video_title}' importiert (~{words} Wörter).\n"
        f"   Datei: {out_path}\n"
        f"   Stevi nutzt dieses Wissen ab dem nächsten Start automatisch."
    )


# ---------------------------------------------------------------------------
# Auflisten + CLI
# ---------------------------------------------------------------------------


def list_imports(knowledge_dir: Path) -> str:
    if not knowledge_dir.is_dir():
        return "Noch kein eigenes Wissen importiert."
    files = sorted(knowledge_dir.glob("*.md"))
    if not files:
        return "Noch kein eigenes Wissen importiert."
    lines = [f"Importiertes Wissen in {knowledge_dir}:"]
    lines += [f"  • {p.name}" for p in files]
    return "\n".join(lines)


_USAGE = """\
Stevi Wissens-Importer — macht Stevi kostenlos schlauer.

Benutzung:
  python -m stevi import mod <ordner-oder-git-url> [Name]
  python -m stevi import transcript <datei.srt|.vtt|.txt> [Titel]
  python -m stevi import list

Beispiele:
  python -m stevi import mod https://github.com/USER/coole-mod.git "Coole Mod"
  python -m stevi import mod ./meine-mod-quellen
  python -m stevi import transcript ./tutorial.vtt "Fabric Items Tutorial"
"""


def run_import_cli(args: list[str]) -> int:
    """Verarbeitet ``stevi import ...`` und gibt einen Exit-Code zurück."""
    config = Config.from_env()
    if not args:
        print(_USAGE)
        return 1

    sub = args[0]
    if sub == "mod":
        if len(args) < 2:
            print("Bitte einen Ordner oder eine Git-URL angeben.\n\n" + _USAGE)
            return 1
        name = args[2] if len(args) > 2 else None
        print(import_mod_source(args[1], config.knowledge_dir, name))
        return 0
    if sub == "transcript":
        if len(args) < 2:
            print("Bitte eine Transkript-Datei angeben.\n\n" + _USAGE)
            return 1
        title = args[2] if len(args) > 2 else None
        print(import_transcript(args[1], config.knowledge_dir, title))
        return 0
    if sub == "list":
        print(list_imports(config.knowledge_dir))
        return 0

    print(f"Unbekannter Import-Befehl: {sub}\n\n" + _USAGE)
    return 1
