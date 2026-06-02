# Minecraft-Konzepte für Modder

## Registries — wie Minecraft Inhalte kennt
Alles im Spiel (Items, Blöcke, Entities, Biome, Sounds …) ist in **Registries**
eingetragen. Beim Modden registrierst du neue Objekte unter einer eindeutigen
**Identifier** (`namespace:pfad`, z.B. `magic_wands:magic_wand`). Der Namespace ist
deine Mod-ID — so kollidieren Mods nicht.

## Identifier (ResourceLocation)
Format `namespace:path`. Beispiele: `minecraft:diamond`, `magic_wands:magic_wand`.
In Yarn (1.21+) erzeugt man sie mit `Identifier.of("magic_wands", "magic_wand")`.

## Client- vs. Server-Seite
Minecraft trennt strikt zwischen **logischem Server** (Spiel-Logik, Welt,
Inventare) und **Client** (Rendering, Eingaben, GUIs). Auch im Singleplayer läuft
intern ein integrierter Server.
- Gemeinsamer Code (`src/main`): Items, Blöcke, Spiel-Logik.
- Client-Code (`src/client`): Renderer, Keybindings, Bildschirme, Partikel.
- Niemals client-only-Klassen aus gemeinsamem Code aufrufen → Crash auf Servern.

## Data-driven: JSON statt Code
Vieles wird über JSON-Dateien definiert (Data Packs / Resource Packs), nicht über
Java:
- **Rezepte**: `data/<mod_id>/recipe/*.json`
- **Loot-Tables**: `data/<mod_id>/loot_table/*.json`
- **Tags**: `data/<mod_id>/tags/...` (z.B. „gehört zu Holz“)
- **Modelle/Blockstates/Texturen**: `assets/<mod_id>/...`
Diese Dateien sind versionsabhängig — Ordnernamen änderten sich z.B. in 1.21.

## Wichtige Objekt-Typen
- **Item**: Gegenstand im Inventar (Werkzeug, Material, Essen …).
- **Block**: platzierbar in der Welt; hat oft ein zugehöriges `BlockItem`.
- **BlockEntity**: Block mit gespeicherten Daten/Logik (z.B. Truhe, Ofen).
- **Entity**: bewegliche Objekte (Mobs, Projektile, Boote).
- **Enchantment / StatusEffect / Biome / Feature**: weitere registrierbare Inhalte.

## Events (Fabric API)
Fabric stellt Events bereit, um an Spielabläufe anzudocken, z.B.:
- `ServerTickEvents` — jeden Server-Tick (20×/Sekunde),
- `UseItemCallback` / `AttackBlockCallback` — Spieler-Interaktionen,
- `ItemGroupEvents` — Items in Kreativtabs einsortieren,
- `ServerLifecycleEvents` — Start/Stop des Servers.

## NBT / Komponenten
Daten an Items/Blöcken werden gespeichert — früher über **NBT**, seit 1.20.5 über
das neue **Data-Component-System** (`ComponentType`). Wenn du Item-Daten brauchst
(z.B. „Ladung des Zauberstabs“), nutzt du Komponenten.

## Ticks und Zeit
- 1 Sekunde = **20 Ticks**.
- 1 Minecraft-Tag = 24000 Ticks (= 20 echte Minuten).
Logik, die „pro Sekunde“ laufen soll, wird also alle 20 Ticks ausgeführt.

## Häufige Anfänger-Themen
- **„Mein Item ist unsichtbar/lila-schwarz“**: Modell oder Textur fehlt/falscher Pfad.
- **„Name wird als `item.magic_wands.magic_wand` angezeigt“**: Sprach-Eintrag in
  `lang/en_us.json` fehlt.
- **„Mod lädt nicht“**: falsche Minecraft-/Loader-Version oder fehlende Fabric API.
- **„Crash beim Server-Start“**: clientseitigen Code im gemeinsamen Teil verwendet.
