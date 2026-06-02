# Item-Eigenschaften, Werkzeuge, Rüstung & Tags (Fabric, MC 1.21.x)

Wichtig: Diese APIs ändern sich zwischen Minecraft-Versionen stark. Die Beispiele
zielen auf **1.21.x**. Prüfe bei Build-Fehlern die genaue Signatur deiner Version
(https://fabricmc.net/develop oder die Yarn-Mappings deiner Version).

## Item.Settings — Eigenschaften eines Items
Items werden über `Item.Settings` konfiguriert (an den Item-Konstruktor übergeben):
```java
new Item.Settings()
    .maxCount(16)            // Stapelgröße (Standard 64)
    .fireproof()             // verbrennt nicht in Feuer/Lava
    .rarity(Rarity.UNCOMMON) // Namensfarbe: COMMON, UNCOMMON, RARE, EPIC
```
`Rarity` liegt in `net.minecraft.util.Rarity`. Diese Settings sind über die 1.21.x-
Reihe relativ stabil.

## Essbares Item (Food)
Achtung versionsabhängig: In 1.21.x wird Essen über eine `FoodComponent` gesetzt.
```java
import net.minecraft.component.type.FoodComponent;

new Item.Settings().food(
    new FoodComponent.Builder()
        .nutrition(4)            // gefüllte Hunger-Häppchen
        .saturationModifier(0.3f)// Sättigung
        .alwaysEdible()          // optional: auch bei vollem Hunger essbar
        .build()
)
```
Hinweis: Die Methodennamen (`saturationModifier`) wurden in einigen 1.21.x-Punkt-
versionen umbenannt — bei einem Fehler die aktuelle Mapping-Signatur prüfen.

## Werkzeuge (Sword, Pickaxe, Axe, Shovel, Hoe)
Werkzeuge brauchen ein `ToolMaterial`. Die ToolMaterial-API ist eine der am
häufigsten geänderten — prüfe deine Version. Grundidee (1.21.x):
```java
// Beispiel mit einem Vanilla-Material; eigenes Material implementiert ToolMaterial.
public static final Item RUBY_SWORD = register("ruby_sword",
    new SwordItem(ToolMaterials.IRON, new Item.Settings()));
public static final Item RUBY_PICKAXE = register("ruby_pickaxe",
    new PickaxeItem(ToolMaterials.IRON, new Item.Settings()));
```
Werkzeug-Items nutzen das Modell `item/handheld` (statt `item/generated`):
```json
{ "parent": "item/handheld", "textures": { "layer0": "mymod:item/ruby_sword" } }
```
Ein eigenes Material implementiert `ToolMaterial` (Abbaustufe, Haltbarkeit, Speed,
Angriffsbonus, Verzauberbarkeit, Reparatur-Zutat).

## Rüstung (Armor)
Rüstung ist in 1.21.2+ stark umgebaut worden (ArmorMaterial ist jetzt eine
registrierte Komponente/`RegistryEntry`). Grobe Idee (genaue Signatur je Version
prüfen):
```java
public static final Item RUBY_HELMET = register("ruby_helmet",
    new ArmorItem(ModArmorMaterials.RUBY, ArmorItem.Type.HELMET, new Item.Settings()));
```
Wegen der starken Versionsunterschiede: erst die Ziel-Version festlegen, dann das
passende ArmorMaterial-Muster verwenden.

## Block-Eigenschaften (AbstractBlock.Settings)
```java
new Block(AbstractBlock.Settings.create()
    .strength(3.0f, 3.0f)   // Härte, Explosionswiderstand
    .requiresTool()         // nur mit passendem Werkzeug abbaubar
    .luminance(state -> 7)) // Lichtstärke 0-15
```

## Tags — Verhalten ohne Code steuern (data/)
Tags gruppieren Blöcke/Items. Sehr nützlich und versionsstabil. Pfad (1.21):
`data/<namespace>/tags/<block|item>/<pfad>.json`
```json
{ "replace": false, "values": ["mymod:ruby_ore"] }
```
Wichtige Vanilla-Block-Tags:
- `minecraft:mineable/pickaxe` (bzw. `axe`, `shovel`, `hoe`) — womit abbaubar.
- `minecraft:needs_stone_tool` / `needs_iron_tool` / `needs_diamond_tool` — Mindeststufe.
Damit ein eigener Block korrekt mit der Spitzhacke abbaubar ist UND einen Iron-Tool
verlangt, in beide Tags eintragen.

Item-Tag-Beispiele: `minecraft:swords`, `minecraft:planks`, `c:ingots` (Common-Tags).
