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

- **LLM-Gehirn:** Anthropic Claude Opus 4.8 — ein extrem fähiges Modell, das
  Programmierung, Java und Minecraft-Konzepte bereits beherrscht.
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
| 💬 **Beraten** | Fragen zu Minecraft, Fabric, Mixins, Modpacks beantworten |
| 📦 **Fabric-Mod erstellen** | Komplettes, kompilierbares Gradle-Projektgerüst anlegen |
| 🧩 **Modpack erstellen** | Modpack-Struktur + Modrinth-Manifest (`modrinth.index.json`) anlegen |
| ➕ **Mods verwalten** | Mods zu einem Modpack hinzufügen / auflisten |

Alle generierten Projekte landen unter `./workspace/` (konfigurierbar).

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
│   ├── __main__.py        # Einstiegspunkt:  python -m stevi
│   ├── cli.py             # Chat-Oberfläche im Terminal
│   ├── agent.py           # Der Agent: verbindet LLM + Wissen + Werkzeuge
│   ├── llm.py             # Claude-Client (Prompt-Caching, Streaming)
│   ├── prompts.py         # Stevis Persönlichkeit & Fachwissen-Systemprompt
│   ├── knowledge.py       # Lädt & durchsucht die Wissensdatenbank
│   ├── config.py          # Einstellungen (API-Key, Modell, Workspace)
│   ├── tools/
│   │   ├── fabric_mod.py  # Fabric-Mod-Gerüst erzeugen
│   │   └── modpack.py     # Modpack erzeugen / verwalten
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
