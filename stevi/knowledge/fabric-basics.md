# Fabric-Modding-Grundlagen

## Was ist Fabric?
Fabric ist eine leichtgewichtige Mod-Plattform für Minecraft (Java Edition). Sie
besteht aus mehreren Teilen:
- **Fabric Loader**: lädt Mods beim Spielstart.
- **Fabric API**: Bibliothek mit Hooks/Events, die fast jede Mod braucht.
- **Yarn Mappings**: lesbare Namen für die (eigentlich obfuskierten) Minecraft-Klassen.
- **Fabric Loom**: das Gradle-Plugin, das Minecraft dekompiliert, Mappings anwendet
  und dein Mod-Projekt baut.

Fabric ist beliebt für moderne Versionen, schnelle Updates und Performance-Mods
(z.B. Sodium). Für KI-generierte Mods gut geeignet, weil die API klar strukturiert ist.

## Projektstruktur einer Fabric-Mod
```
mein-mod/
├── build.gradle            # Gradle-Build, Loom-Plugin, Abhängigkeiten
├── gradle.properties       # Versionen (Minecraft, Loader, Yarn, Fabric API)
├── settings.gradle         # Fabric-Maven-Repository
└── src/
    ├── main/
    │   ├── java/...        # gemeinsamer Code (Server + Client)
    │   └── resources/
    │       ├── fabric.mod.json     # Metadaten + Einstiegspunkte
    │       ├── <mod_id>.mixins.json # Mixin-Konfiguration
    │       └── assets/<mod_id>/...  # Texturen, Modelle, Sprachdateien
    └── client/
        └── java/...        # nur Client (Rendering, Keybindings, GUIs)
```

## fabric.mod.json — die wichtigste Metadaten-Datei
Definiert ID, Name, Version, Einstiegspunkte und Abhängigkeiten. Beispiel:
```json
{
  "schemaVersion": 1,
  "id": "magic_wands",
  "version": "${version}",
  "name": "Magic Wands",
  "entrypoints": {
    "main": ["com.example.magicwands.MagicWandsMod"],
    "client": ["com.example.magicwands.MagicWandsClientMod"]
  },
  "depends": { "fabricloader": ">=0.16.0", "minecraft": "*", "fabric-api": "*" }
}
```
- **main**-Einstiegspunkt: Klasse mit `implements ModInitializer` → `onInitialize()`.
- **client**-Einstiegspunkt: Klasse mit `implements ClientModInitializer` → `onInitializeClient()`.

## Ein eigenes Item registrieren
Items werden im `onInitialize()` registriert. Grobes Muster (Yarn, MC 1.21.x):
```java
public class MagicWandsMod implements ModInitializer {
    public static final String MOD_ID = "magic_wands";

    public static final Item MAGIC_WAND = Registry.register(
        Registries.ITEM,
        Identifier.of(MOD_ID, "magic_wand"),
        new Item(new Item.Settings())
    );

    @Override
    public void onInitialize() {
        // In ein Kreativtab einsortieren:
        ItemGroupEvents.modifyEntriesEvent(ItemGroups.TOOLS)
            .register(entries -> entries.add(MAGIC_WAND));
    }
}
```
Für das Item brauchst du außerdem:
- ein **Modell** unter `assets/<mod_id>/models/item/magic_wand.json`,
- eine **Textur** unter `assets/<mod_id>/textures/item/magic_wand.png`,
- einen **Sprach-Eintrag** in `assets/<mod_id>/lang/en_us.json`
  (`"item.magic_wands.magic_wand": "Magic Wand"`).

## Einen eigenen Block registrieren
Ähnlich wie Items, aber über `Registries.BLOCK` und meist zusätzlich ein
zugehöriges `BlockItem`. Blöcke brauchen Blockstate-, Modell- und Loot-Table-Dateien.

## Mixins — in Minecraft-Code eingreifen
Ein **Mixin** erlaubt es, bestehende Minecraft-Methoden zu verändern/zu erweitern,
ohne den Quellcode zu kopieren. Mixins stehen in der `<mod_id>.mixins.json` und sind
Java-Klassen mit `@Mixin`-Annotation und `@Inject`/`@Redirect`-Hooks. Mächtig, aber
mit Vorsicht zu verwenden — sie können mit anderen Mods kollidieren.

## Bauen und Testen
- `./gradlew build` → fertige `.jar` in `build/libs/`.
- `./gradlew runClient` → startet Minecraft mit der Mod zum Testen.
- `./gradlew runServer` → startet einen Testserver.
Java 21 wird für aktuelle Minecraft-Versionen (1.20.5+) benötigt.

## Versionen aktuell halten
Die exakten Versionsnummern (Minecraft, Yarn, Loader, Fabric API) ändern sich
ständig. Aktuelle Werte stehen auf https://fabricmc.net/develop — dort den
gewünschten Minecraft-Versions-Tab wählen und die Zeilen in `gradle.properties`
übernehmen.
