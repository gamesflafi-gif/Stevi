"""Terminal-Chat-Oberfläche für Stevi.

Start:  python -m stevi   (oder  stevi  nach der Installation)
"""

from __future__ import annotations

import sys
from typing import Any

from .agent import Agent
from .config import Config

GREEN = "\033[92m"
GREY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

BANNER = f"""{GREEN}{BOLD}
   ____  _              _
  / ___|| |_ _____   __(_)
  \\___ \\| __/ _ \\ \\ / /| |
   ___) | ||  __/\\ V / | |
  |____/ \\__\\___| \\_/  |_|   🟩  Die Minecraft-Modding-KI
{RESET}"""

HELP = f"""{GREY}Befehle:
  /help     diese Hilfe anzeigen
  /reset    Gespräch zurücksetzen
  /quit     beenden  (oder Strg+D)
{RESET}"""


def _on_text(delta: str) -> None:
    sys.stdout.write(delta)
    sys.stdout.flush()


def _on_tool(name: str, tool_input: dict[str, Any]) -> None:
    # Werkzeug-Nutzung sichtbar machen (in grau, in einer eigenen Zeile).
    sys.stdout.write(f"\n{GREY}🛠️  führe Werkzeug aus: {name}{RESET}\n")
    sys.stdout.flush()


def run_chat() -> int:
    """Startet die interaktive Chat-Schleife. Gibt einen Exit-Code zurück."""
    config = Config.from_env()
    try:
        agent = Agent(config)
    except RuntimeError as exc:
        print(f"{exc}", file=sys.stderr)
        return 1

    print(BANNER)
    print(
        f"{GREEN}🟩 Stevi:{RESET} Hi! Ich bin Stevi, deine Minecraft-Modding-KI. "
        f"Ich kann über Minecraft & Fabric reden und dir echte Mods/Modpacks bauen.\n"
        f"        Was sollen wir machen?"
    )
    print(HELP)
    print(f"{GREY}Modell: {config.model} · Workspace: {config.workspace}{RESET}\n")

    while True:
        try:
            user_input = input(f"{BOLD}Du:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBis bald! 🟩")
            return 0

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("/quit", "/exit", "/q"):
            print("Bis bald! 🟩")
            return 0
        if cmd == "/help":
            print(HELP)
            continue
        if cmd == "/reset":
            agent.messages.clear()
            print(f"{GREY}Gespräch zurückgesetzt.{RESET}")
            continue

        # Stevis Antwort wird live gestreamt.
        print(f"{GREEN}🟩 Stevi:{RESET} ", end="")
        try:
            agent.send(user_input, on_text=_on_text, on_tool=_on_tool)
        except Exception as exc:  # pragma: no cover - Laufzeit-/Netzwerkfehler
            print(f"\n{GREY}[Fehler: {exc}]{RESET}")
        print("\n")


def main() -> None:
    """Einstiegspunkt für das Konsolen-Skript ``stevi``."""
    raise SystemExit(run_chat())


if __name__ == "__main__":
    main()
