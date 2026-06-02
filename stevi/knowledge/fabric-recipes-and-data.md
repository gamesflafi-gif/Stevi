# Rezepte, Loot & Data Packs (Fabric)

Viele Inhalte werden in Minecraft über **JSON-Dateien** definiert, nicht über Java.
Diese liegen im `data/<mod_id>/`-Ordner deiner Mod (Server-/Data-Pack-Seite) bzw.
`assets/<mod_id>/` (Client-/Resource-Pack-Seite). Wichtig: Die Ordnernamen sind
**versionsabhängig** — in Minecraft 1.21 wurden einige in die Einzahl geändert
(z.B. `recipe`, `loot_table` statt früher `recipes`, `loot_tables`).

## Crafting-Rezepte
Pfad: `data/<mod_id>/recipe/<name>.json`

### Geformtes Rezept (shaped)
```json
{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    " S ",
    " S ",
    " D "
  ],
  "key": {
    "S": { "item": "minecraft:stick" },
    "D": { "item": "minecraft:diamond" }
  },
  "result": { "id": "magic_wands:magic_wand", "count": 1 }
}
```
- `pattern`: bis zu 3 Zeilen à 3 Zeichen. Leerzeichen = leeres Feld.
- `key`: ordnet jedem Zeichen ein Item zu.
- `result`: seit 1.20.5 mit `"id"` (vorher `"item"`).

### Formloses Rezept (shapeless)
```json
{
  "type": "minecraft:crafting_shapeless",
  "ingredients": [
    { "item": "minecraft:diamond" },
    { "item": "minecraft:stick" }
  ],
  "result": { "id": "magic_wands:magic_wand", "count": 1 }
}
```

### Weitere Rezepttypen
`minecraft:smelting` (Ofen), `minecraft:blasting`, `minecraft:smoking`,
`minecraft:campfire_cooking`, `minecraft:stonecutting`, `minecraft:smithing_transform`.

## Loot-Tables (was droppt ein Block/Mob)
Pfad für Blöcke: `data/<mod_id>/loot_table/blocks/<name>.json`
```json
{
  "type": "minecraft:block",
  "pools": [
    {
      "rolls": 1,
      "entries": [
        { "type": "minecraft:item", "name": "magic_wands:ruby" }
      ]
    }
  ]
}
```
Ohne Loot-Table droppt ein Block nichts. Für „droppt sich selbst" trägst du die
eigene Block-ID als Item ein.

## Tags (Gruppen von Blöcken/Items)
Pfad: `data/<mod_id>/tags/...` bzw. um Vanilla-Tags zu ergänzen
`data/minecraft/tags/...`. Beispiel „mein Block ist mit der Spitzhacke abbaubar":
`data/minecraft/tags/block/mineable/pickaxe.json`
```json
{ "replace": false, "values": ["magic_wands:ruby_ore"] }
```

## Modelle & Texturen (Client-Seite, assets/)
- Item-Modell: `assets/<mod_id>/models/item/<name>.json`
  ```json
  { "parent": "item/generated", "textures": { "layer0": "magic_wands:item/ruby" } }
  ```
- Block-Modell: `assets/<mod_id>/models/block/<name>.json` (oft `parent: block/cube_all`).
- Blockstate: `assets/<mod_id>/blockstates/<name>.json` verweist auf das Block-Modell.
- Texturen sind PNGs unter `assets/<mod_id>/textures/item|block/<name>.png` (16x16).
- Sprache: `assets/<mod_id>/lang/en_us.json` (`"item.magic_wands.ruby": "Ruby"`).

## Datengetriebenes Neuladen
Im Spiel kannst du Data-Pack-Inhalte (Rezepte, Loot, Tags) mit `/reload` neu laden,
ohne Minecraft neu zu starten. Assets (Texturen/Modelle) brauchen meist F3+T.
