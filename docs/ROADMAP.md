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

## Phase 2 — Mehr Wissen & Inhalte 🔄 (in Arbeit)
- ✅ **Wissens-Importer:** `stevi import mod <ordner|git-url>` und
  `stevi import transcript <datei>` nehmen echten Mod-Quellcode und
  Video-Transkripte (als Text!) in die Wissensdatenbank auf. So lernt Stevi aus
  Tutorials — ohne die Videos pixelweise „anzuschauen" (das wäre teuer und
  schlechter). Importiertes Wissen wird automatisch mitgeladen.
- ✅ **Werkzeug „Item/Block hinzufügen":** `add_item` / `add_block` erzeugen
  automatisch Java-Registrierung (regenerierte ModItems/ModBlocks), Modell-/
  Blockstate-/Loot-/Lang-JSON, Platzhalter-Textur und klinken `initialize()` in die
  Hauptklasse ein.
- 🔜 Kuratierte Wissensdatenbank ausbauen: Fabric-API-Referenzen, mehr
  Beispiel-Snippets (Entity, Rezept), häufige Crash-Ursachen.
- 🔜 Forge/NeoForge-Unterstützung als Option.
- 🔜 Versionsnummern automatisch von fabricmc.net beziehen (statt fester Defaults).

## Phase 3 — Echtes Bauen & Selbstkorrektur ✅ (erledigt)
- ✅ Werkzeug `build_mod`: führt `./gradlew build` (oder `gradle build`) aus und gibt
  Erfolg oder die Fehlerausgabe zurück.
- ✅ Stevi liest Compiler-/Gradle-Fehler und kann in seiner Werkzeug-Schleife
  eigenständig nachbessern (read_mod_file → write_mod_file → build_mod).
- 🔜 Gradle-Wrapper automatisch erzeugen (aktuell Hinweis: einmalig `gradle wrapper`).

## Phase 4 — Bestehende Mods analysieren & umschreiben ✅ (erledigt)
- ✅ `analyze_mod`: Mod-Struktur einlesen und verstehen (Metadaten, Registrierungen,
  Dateiübersicht).
- ✅ `read_mod_file` / `write_mod_file`: einzelne Dateien gezielt ansehen und
  umschreiben (sicher auf das Projekt beschränkt) — „Schreibe Mod X so um, dass …".
- ✅ `add_mixin`: Mixin-Gerüst für Eingriffe ins Vanilla-Verhalten, inkl. Eintrag in
  die mixins.json.

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
