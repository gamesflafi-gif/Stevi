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

## Laufende Verbesserungen (weniger Fehler, mehr Möglichkeiten) 🔄
- ✅ `add_item` mit Eigenschaften: Stapelgröße, feuerfest, Seltenheit.
- ✅ `add_tag`: Blöcke/Items zu Tags hinzufügen (z.B. mit Spitzhacke abbaubar).
- ✅ `validate_mod`: findet fehlende Modelle/Texturen/Lang/Loot/Mixins vor dem Bauen.
- ✅ CI (GitHub Actions): Testsuite läuft bei jedem Push/PR (Python 3.10–3.12).
- ✅ Mehr Wissen: Item-Settings, Werkzeuge/Rüstung, Tags (version-bewusst).
- 🔜 Weitere Generatoren: Werkzeuge/Rüstung/Food als eigene Werkzeuge (version-robust).

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

## Phase 5 — Ausliefern & Auflösen ✅ (Kern erledigt)
- ✅ `add_mod_from_modrinth`: Mod-Suche/Resolver — holt Mods von Modrinth mit echtem
  Download-Link, Hashes und Dateigröße (gültiger .mrpack-Eintrag).
- ✅ `export_modpack`: erzeugt die fertige `.mrpack`-Datei (ZIP) zum direkten Import
  in Prism Launcher / Modrinth App (inkl. `overrides/`).
- ✅ `validate_modpack`: prüft das Manifest vor dem Export (Loader/Version, doppelte
  Pfade, Mods ohne Quelle).
- ✅ `search_modrinth`: Mods auf Modrinth durchsuchen (Name → Slug).
- ✅ Abhängigkeiten automatisch mit auflösen: `add_mod_from_modrinth` zieht benötigte
  Dependencies (z.B. Fabric API) gleich mit.
- ✅ `add_recipe`: Crafting-Rezepte (shaped/shapeless) generieren.
- 🔜 Mods/Modpacks in einer echten Test-Instanz starten — braucht eine echte
  Spielumgebung (außerhalb eines headless-Servers); `build_mod` + `validate_modpack`
  decken die praktische „Hält alles zusammen?"-Prüfung ab.

---

## Technische Ideen für später
- **Echtes Embedding-RAG** (Vektor-Suche) statt Schlagwort-Suche, sobald die
  Wissensbasis groß wird.
- **Fine-Tuning** eines offenen Modells auf Minecraft-Modding-Daten als optionaler
  Zusatz — nur sinnvoll, wenn genug kuratierte Trainingsdaten vorliegen.
- **MCP-Server / Managed Agents**, damit Stevi in einer Sandbox eigenständig baut
  und testet.
