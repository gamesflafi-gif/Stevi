# 🗺️ Stevi — Roadmap

Stevi soll Schritt für Schritt zur vollwertigen Minecraft-Modding-KI wachsen. Hier
der Plan, von „funktioniert heute“ bis zur großen Vision.

## Vision
Du beschreibst dein Wunsch-Modpack oder deine Wunsch-Mod in normaler Sprache, und
Stevi baut es so, dass es in Minecraft läuft und spielbar ist — inklusive eigener
Items, Blöcke, Mechaniken und einer passenden Mod-Auswahl.

---

## Phase 1 — Fundament ✅ (erledigt)
- Chat-Agent mit **umschaltbarem Backend**: lokal/kostenlos via **Ollama** oder
  Claude-API.
- **Web-Chat-Terminal** (`python -m stevi web`) — server-tauglich, im Browser
  erreichbar, ohne externe API-Kosten.
- Minecraft-/Fabric-Wissensdatenbank (RAG) — erweiterbar ohne Neutraining.
- Werkzeuge: komplettes Fabric-Mod-Gradle-Projekt erzeugen, Modpack mit
  Modrinth-Manifest erzeugen, Mods hinzufügen, Workspace auflisten.
- Tests für Werkzeuge, Wissenssuche und Backends.

## Phase 2 — Mehr Wissen & Inhalte 🔜
- Wissensdatenbank ausbauen: Fabric-API-Referenzen, Beispiel-Snippets (Item, Block,
  BlockEntity, Entity, Rezept, Loot-Table), häufige Crash-Ursachen.
- **Wissen aus echten Mods & Videos (als Text!):** Werkzeug, das öffentlichen
  Mod-Quellcode (GitHub) und **Video-Transkripte/Untertitel** einliest und in die
  Wissensdatenbank aufnimmt. So lernt Stevi aus Tutorials — ohne die Videos
  pixelweise „anzuschauen" (das wäre teuer und schlechter).
- Werkzeug „Item/Block hinzufügen“: erzeugt automatisch Java-Registrierung +
  Modell-/Blockstate-/Lang-JSON + Platzhalter-Textur.
- Forge/NeoForge-Unterstützung als Option.
- Versionsnummern automatisch von fabricmc.net beziehen (statt fester Defaults).

## Phase 3 — Echtes Bauen & Selbstkorrektur
- Werkzeug `build_mod`: führt `./gradlew build` aus und gibt das Ergebnis zurück.
- Stevi liest Compiler-/Gradle-Fehler und behebt sie eigenständig (Schleife).
- Gradle-Wrapper automatisch erzeugen, damit Projekte ohne lokale Gradle-Installation
  bauen.

## Phase 4 — Bestehende Mods analysieren & umschreiben
- Mod-Quellcode einlesen, Struktur verstehen, gezielt anpassen.
- „Schreibe Mod X so um, dass …“ — z.B. Rezepte ändern, Werte balancen, Features
  ergänzen.
- Mixin-Generierung für Eingriffe in Vanilla-Verhalten.

## Phase 5 — Testen & Ausliefern
- Mods/Modpacks in einer Test-Instanz automatisch starten und auf Crashes prüfen.
- Modpack-Export als fertige `.mrpack`-Datei (ZIP) zum direkten Import.
- Mod-Suche/Resolver: Mods + Abhängigkeiten von Modrinth automatisch auflösen.

---

## Technische Ideen für später
- **Echtes Embedding-RAG** (Vektor-Suche) statt Schlagwort-Suche, sobald die
  Wissensbasis groß wird.
- **Fine-Tuning** eines offenen Modells auf Minecraft-Modding-Daten als optionaler
  Zusatz — nur sinnvoll, wenn genug kuratierte Trainingsdaten vorliegen.
- **MCP-Server / Managed Agents**, damit Stevi in einer Sandbox eigenständig baut
  und testet.
