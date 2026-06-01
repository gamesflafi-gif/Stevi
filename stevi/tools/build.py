"""Phase-3-Werkzeug: eine Mod tatsächlich bauen (Gradle).

Führt ``./gradlew build`` (oder ``gradle build``) im Projektordner aus und gibt
Erfolg oder den Fehler-Ausschnitt zurück. Schlägt der Build fehl, kann Stevi den
Fehler lesen und in seiner Werkzeug-Schleife selbst nachbessern.

Voraussetzung zur Laufzeit: ein JDK (21 für aktuelle Minecraft-Versionen) und
entweder ein Gradle-Wrapper im Projekt oder eine Gradle-Installation. Fehlt beides,
gibt das Werkzeug einen klaren Hinweis zurück (statt zu crashen).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import project as P

BUILD_TIMEOUT = 1800           # Sekunden (Gradle kann beim ersten Lauf lange dauern)
MAX_OUTPUT_CHARS = 4000        # so viel Build-Ausgabe geben wir zurück


def resolve_build_command(project: Path) -> tuple[list[str] | None, str]:
    """Bestimmt das Build-Kommando. Gibt (cmd, fehlermeldung) zurück."""
    gradlew = project / ("gradlew.bat" if os.name == "nt" else "gradlew")
    if gradlew.is_file():
        if os.name != "nt":
            try:
                gradlew.chmod(gradlew.stat().st_mode | 0o111)  # ausführbar machen
            except OSError:
                pass
        return [str(gradlew), "build", "--no-daemon"], ""
    if shutil.which("gradle"):
        return ["gradle", "build", "--no-daemon"], ""
    return None, (
        "Weder ein Gradle-Wrapper (./gradlew) noch eine Gradle-Installation gefunden.\n"
        "Installiere Gradle + ein JDK 21, oder erzeuge den Wrapper einmalig im "
        "Projektordner mit:  gradle wrapper"
    )


def _tail(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    return text if len(text) <= limit else "…(gekürzt)…\n" + text[-limit:]


def build_mod(tool_input: dict[str, Any], workspace: Path) -> str:
    mod_identifier = tool_input["mod"].strip()
    project = P.find_project(workspace, mod_identifier)
    if project is None:
        return f"Keine Mod '{mod_identifier}' im Workspace gefunden."

    cmd, err = resolve_build_command(project)
    if cmd is None:
        return err

    try:
        proc = subprocess.run(
            cmd,
            cwd=project,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return f"Der Build hat das Zeitlimit ({BUILD_TIMEOUT}s) überschritten."
    except OSError as exc:
        return f"Build konnte nicht gestartet werden: {exc}"

    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0:
        jars = list((project / "build" / "libs").glob("*.jar")) if (project / "build/libs").is_dir() else []
        jar_note = (
            "\n   Fertige Datei(en): "
            + ", ".join(str(j.relative_to(project)) for j in jars)
            if jars
            else ""
        )
        return f"✅ Build erfolgreich für '{project.name}'.{jar_note}"

    return (
        f"❌ Build fehlgeschlagen (Exit-Code {proc.returncode}) für '{project.name}'.\n"
        f"--- Ausgabe (Ende) ---\n{_tail(output)}"
    )
