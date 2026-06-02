# 🟩 Stevi — Die Minecraft-Modding-KI

**Stevi** ist ein KI-Chatbot, der komplett auf Minecraft spezialisiert ist. Er kennt
sich mit dem Spiel, mit Mod-Programmierung (Fabric), mit Modpacks und ihrer
Erstellung aus — und kann auf Wunsch **selbst spielbare Fabric-Mods und Modpacks
generieren**, die in Minecraft funktionieren.

> Du sagst, was dein Modpack können soll — Stevi baut es.

---

## 🧠 Wie Stevi funktioniert (Architektur)

Ein eigenes KI-Modell von Grund auf zu trainieren würde Monate, große GPU-Cluster
und sechsstellige Kosten bedeuten — und wäre am Ende schlechter als ein
spezialisierter Agent auf einem Spitzenmodell. Stevi nimmt deshalb den schnelleren,
besseren Weg:

```
┌─────────────────────────────────────────────────────────────┐
│                          STEVI                               │
│                                                              │
│   Du (Chat)  ─►  Agent  ─►  Claude Opus 4.8 (LLM-Gehirn)     │
│                    │                                         │
│                    ├─►  📚 Minecraft-Wissensdatenbank (RAG)  │
│                    │       Fabric, Modpacks, MC-Konzepte     │
│                    │                                         │
│                    └─►  🛠️  Werkzeuge                         │
│                            • Fabric-Mod erstellen            │
│                            • Modpack erstellen               │
│                            • Mods zum Modpack hinzufügen     │
└─────────────────────────────────────────────────────────────┘
```

- **LLM-Gehirn (umschaltbar):** Stevi kann zwei „Gehirne" nutzen:
  - 🆓 **Ollama (lokal/selbst-gehostet)** — ein Open-Source-Modell auf deinem
    eigenen Server. **Kostenlos, offline, ohne API-Schlüssel.** Empfohlen, wenn du
    keine laufenden Kosten willst.
  - ☁️ **Claude Opus 4.8 (Anthropic-API)** — stärker, aber kostenpflichtig.
  Welches verwendet wird, steuerst du mit `STEVI_BACKEND`. Das ganze restliche
  Gerüst (Wissen, Werkzeuge) bleibt identisch.
- **Wissensdatenbank (RAG):** Kuratierte Minecraft-/Fabric-Modding-Dokumentation
  unter `stevi/knowledge/`. Bei jeder Frage werden die relevanten Abschnitte
  herausgesucht und Stevi mitgegeben — so bleibt das Wissen aktuell und erweiterbar,
  **ohne neu zu trainieren**.
- **Werkzeuge:** Stevi kann nicht nur reden, sondern echte Projekte auf die
  Festplatte schreiben — komplette Fabric-Mod-Gradle-Projekte und Modpack-Strukturen.

So hast du **sofort** einen funktionierenden, Minecraft-spezialisierten Stevi, den
wir Schritt für Schritt mit mehr Wissen und Fähigkeiten erweitern.

---

## 🚀 Schnellstart

### 1. Voraussetzungen

- Python 3.10 oder neuer
- Ein Anthropic-API-Schlüssel — bekommst du auf <https://console.anthropic.com>

### 2. Installation

```bash
git clone <dieses-repo>
cd Stevi
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. API-Schlüssel setzen

```bash
cp .env.example .env
# Öffne .env und trage deinen Schlüssel ein:
# ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Mit Stevi chatten

```bash
python -m stevi
```

---

## 🆓 Kostenlos & selbst-gehostet (ohne API-Kosten)

Du willst **keine laufenden Kosten** und Stevi auf deinem **eigenen Server** mit
**Web-Terminal** betreiben? So geht's:

### Schritt 1 — Ollama installieren & Modell ziehen

[Ollama](https://ollama.com) ist ein kostenloser Runner für lokale Modelle.

```bash
# Ollama installieren (siehe https://ollama.com), dann ein Code-Modell ziehen:
ollama pull qwen2.5-coder:7b     # gut auf GPU mit ~8 GB; kleinere Alternative: :1.5b
ollama serve                     # startet den lokalen Modell-Server
```

> Modell-Größe nach Hardware wählen: `:1.5b` (schwacher PC), `:7b` (GPU 8 GB),
> `:14b`/`:32b` (mehr VRAM = schlauer). Werkzeug-Aufrufe brauchen ein
> tools-fähiges Modell (z.B. `qwen2.5-coder`, `llama3.1`).

### Schritt 2 — Stevi auf das lokale Modell stellen

In `.env`:

```bash
STEVI_BACKEND=ollama
STEVI_OLLAMA_MODEL=qwen2.5-coder:7b
```

### Schritt 3 — Web-Terminal starten

```bash
python -m stevi web                 # nur lokal:  http://127.0.0.1:8000
python -m stevi web 0.0.0.0 8000    # im Netz/Server erreichbar
```

Öffne die Adresse im Browser und chatte mit Stevi — komplett kostenlos, ohne
externe API. 🎉

> ⚠️ **Sicherheit:** Das Web-Terminal hat keine Anmeldung. Mach es nur in einem
> vertrauenswürdigen Netz auf, oder setze einen Reverse-Proxy mit Passwort davor,
> wenn es öffentlich erreichbar sein soll.

### Lohnt sich ein eigenes Modell „aus Videos"?

Kurz: **nein.** Ein Modell von Grund auf mit Videos zu trainieren ist für
Einzelpersonen praktisch unmöglich (Millionenkosten, riesige GPU-Cluster) und
liefert schlechtere Ergebnisse. Das wertvolle Wissen aus Modding-Videos steckt im
**Code** — und der ist frei als Text verfügbar. Stevi nutzt deshalb ein fertiges,
lokales Modell + eine wachsende Wissensdatenbank (in die wir Mod-Code und sogar
Video-**Transkripte** als Text laden können). Details: [`docs/ROADMAP.md`](docs/ROADMAP.md).

Beispiel-Unterhaltung:

```
🟩 Stevi: Hi! Ich bin Stevi, deine Minecraft-Modding-KI. Was sollen wir bauen?

Du: Erstelle mir eine Fabric-Mod namens "Magic Wands" für Minecraft 1.21,
    die einen neuen Zauberstab als Item hinzufügt.

🟩 Stevi: Klar! Ich lege ein komplettes Fabric-Gradle-Projekt an ...
          [erstellt build.gradle, fabric.mod.json, MagicWandsMod.java, ...]
```

---

## 🛠️ Was Stevi heute kann

| Fähigkeit | Beschreibung |
|-----------|--------------|
| 🆓 **Kostenlos laufen** | Lokales Modell via Ollama — keine API-Kosten |
| 🌐 **Web-Terminal** | Im Browser chatten (`python -m stevi web`), server-tauglich |
| 💬 **Beraten** | Fragen zu Minecraft, Fabric, Mixins, Modpacks beantworten |
| 📦 **Fabric-Mod erstellen** | Komplettes, kompilierbares Gradle-Projektgerüst anlegen |
| 🧱 **Items & Blöcke** | Items/Blöcke in eine Mod generieren (Java + JSON + Textur + Loot) |
| 📜 **Rezepte** | Crafting-Rezepte (shaped/shapeless) als data-JSON erzeugen |
| 🔨 **Bauen** | Mod mit Gradle bauen, Fehler lesen und selbst nachbessern |
| 🔍 **Analysieren & umschreiben** | Mods analysieren, Dateien lesen/schreiben, Mixins erzeugen |
| 🧩 **Modpack erstellen** | Modpack-Struktur + Modrinth-Manifest (`modrinth.index.json`) anlegen |
| 🔎 **Mods finden** | Modrinth durchsuchen, um den richtigen Mod zu finden |
| 🔗 **Mods auflösen** | Mods + Abhängigkeiten von Modrinth holen (Download-Link + Hashes) |
| 📤 **Exportieren** | Fertige `.mrpack`-Datei für Prism Launcher / Modrinth App |
| 🧠 **Dazulernen** | Mod-Code & Video-Transkripte importieren (`stevi import …`) |

Alle generierten Projekte landen unter `./workspace/` (konfigurierbar).

---

## 🧠 Stevi schlauer machen (Wissen importieren)

Stevi lernt dazu, indem du echtes Material als **Text** in seine Wissensdatenbank
lädst — **kostenlos, ohne Training**. Das importierte Wissen wird beim nächsten
Start automatisch mitgenutzt (Suche per Stichwort, RAG).

```bash
# Echten Mod-Quellcode importieren (lokaler Ordner ODER GitHub-URL):
python -m stevi import mod https://github.com/USER/coole-mod.git "Coole Mod"
python -m stevi import mod ./meine-mod-quellen

# Video-Transkript / Untertitel importieren (.srt, .vtt oder .txt):
python -m stevi import transcript ./tutorial.vtt "Fabric Items Tutorial"

# Anzeigen, was schon importiert wurde:
python -m stevi import list
```

> **Warum Transkripte statt Videos?** Das wertvolle Wissen in einem Tutorial ist die
> Erklärung und der **Code**, nicht das Bild. Untertitel (oft per Klick als `.srt`/
> `.vtt` ladbar) liefern genau diesen Text — viel effizienter und ohne teures
> Video-Training. YouTube-Untertitel kannst du z.B. mit Tools wie `yt-dlp` als
> `.vtt` herunterladen und dann importieren.

---

## 🗺️ Roadmap — Stevi wird schlauer

- [x] **Phase 1 — Fundament:** Chat-Agent + Wissensdatenbank + Mod-/Modpack-Gerüste
- [ ] **Phase 2 — Mehr Wissen:** Fabric-API-Referenzen, Beispielmods, Forge/NeoForge
- [ ] **Phase 3 — Echtes Bauen:** `gradle build` automatisch ausführen, Fehler selbst beheben
- [ ] **Phase 4 — Mods umschreiben:** Bestehende Mods analysieren und gezielt anpassen
- [ ] **Phase 5 — Testen:** Mods in einer Test-Instanz automatisch starten und prüfen

Details siehe [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## 📁 Projektstruktur

```
Stevi/
├── stevi/
│   ├── __main__.py        # Einstiegspunkt:  python -m stevi  [web]
│   ├── cli.py             # Chat-Oberfläche im Terminal
│   ├── web.py             # 🌐 Web-Chat-Terminal (Browser, server-tauglich)
│   ├── agent.py           # Der Agent: verbindet Backend + Wissen + Werkzeuge
│   ├── backends/          # 🔌 Umschaltbare "Gehirne"
│   │   ├── ollama.py      #    lokal/kostenlos
│   │   └── claude.py      #    Anthropic-API
│   ├── prompts.py         # Stevis Persönlichkeit & Fachwissen-Systemprompt
│   ├── knowledge.py       # Lädt & durchsucht die Wissensdatenbank
│   ├── knowledge_import.py# 🧠 Mod-Code & Transkripte importieren
│   ├── config.py          # Einstellungen (Backend, Modell, Workspace)
│   ├── tools/
│   │   ├── fabric_mod.py  # Fabric-Mod-Gerüst erzeugen
│   │   ├── modpack.py     # Modpack erzeugen / verwalten
│   │   ├── project.py     # geteilte Projekt-Helfer (finden, Manifest, Texturen)
│   │   ├── content.py     # Items & Blöcke generieren (Phase 2)
│   │   ├── build.py       # Mod mit Gradle bauen (Phase 3)
│   │   ├── analyze.py     # analysieren / Dateien lesen+schreiben (Phase 4)
│   │   ├── mixin.py       # Mixin-Gerüste erzeugen (Phase 4)
│   │   └── distribute.py  # Modrinth-Auflösung + .mrpack-Export (Phase 5)
│   └── knowledge/         # 📚 Markdown-Wissensdatenbank
│       ├── fabric-basics.md
│       ├── modpack-basics.md
│       └── minecraft-concepts.md
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚠️ Hinweis zu Minecraft-Versionen & APIs

Minecraft-Modding ändert sich von Version zu Version. Stevi erzeugt Gerüste für
**Fabric** (moderne, beliebte Mod-Plattform). Die genauen Versionsnummern von
Minecraft, Fabric Loader, Fabric API und Yarn-Mappings müssen ggf. an die jeweils
aktuelle Version angepasst werden — Stevi weist dich darauf hin und du kannst sie
in `gradle.properties` leicht ändern.

---

## 📜 Lizenz

Noch festzulegen. Bis dahin: privates Lern-/Entwicklungsprojekt.
