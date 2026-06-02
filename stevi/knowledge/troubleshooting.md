# Fehlersuche: häufige Modding- & Modpack-Probleme

## Mod lädt gar nicht
- **Falsche Minecraft-/Loader-Version**: Eine 1.20.1-Mod lädt nicht in 1.21.1.
  Prüfe `fabric.mod.json` (`depends`) und die Jar gegen die Instanz-Version.
- **Fehlende Fabric API**: Viele Mods brauchen sie. Stürzt mit
  `requires fabric-api` ab → Fabric API passend zur MC-Version installieren.
- **Fabric- vs. Forge-Mod verwechselt**: Eine Forge-Jar läuft NICHT unter Fabric.

## Build schlägt fehl (Gradle)
- **`Unsupported class file major version` / Java-Fehler**: Falsche Java-Version.
  Aktuelle Minecraft-Versionen (1.20.5+) brauchen **JDK 21**. Prüfe `JAVA_HOME`.
- **`Could not resolve net.fabricmc...`**: Versionsnummern in `gradle.properties`
  stimmen nicht. Aktuelle Werte von https://fabricmc.net/develop übernehmen.
- **`cannot find symbol` / Methode existiert nicht**: API hat sich zwischen
  Versionen geändert (z.B. `Item`-Konstruktor, `Identifier.of` vs. `new Identifier`).
  An die Ziel-Version anpassen.
- **Erster Build dauert lange**: normal — Loom lädt und dekompiliert Minecraft.

## Item/Block ist im Spiel kaputt
- **Schwarz-lila Textur / unsichtbar**: Modell oder Textur fehlt oder hat den
  falschen Pfad. Item braucht `models/item/<name>.json` + `textures/item/<name>.png`.
- **Name zeigt `item.mod_id.name` statt echtem Namen**: Sprach-Eintrag in
  `lang/en_us.json` fehlt.
- **Block droppt nichts**: Loot-Table fehlt
  (`data/<mod_id>/loot_table/blocks/<name>.json`).
- **Block lässt sich nur langsam/ohne Werkzeug abbauen**: passenden `mineable`-Tag
  setzen (z.B. `mineable/pickaxe`).
- **Block hat keine Kollision/falsche Härte**: über `AbstractBlock.Settings`
  konfigurieren (strength, hardness, resistance).

## Crash beim Start
- **`NoClassDefFoundError` / clientseitige Klasse auf dem Server**: Client-only-Code
  (Rendering, `MinecraftClient`) darf NICHT aus dem gemeinsamen `src/main` aufgerufen
  werden — gehört in `src/client`.
- **Mixin-Crash (`Mixin apply failed`)**: Ziel-Methode/Deskriptor stimmt nicht mit
  der Mappings-/MC-Version überein, oder zwei Mods kollidieren am selben Ziel.
- **Den Crash-Report lesen**: Die Zeile nach „Caused by:" nennt meist die echte
  Ursache und die verantwortliche Mod.

## Modpack-Probleme
- **Crash beim Laden des Packs**: per Halbierung eingrenzen — die Hälfte der Mods
  entfernen, testen, weiter eingrenzen, bis der Übeltäter feststeht.
- **Zwei Mods machen dasselbe**: z.B. nicht Sodium UND OptiFine. Doppelte
  Renderer/Optimierer kollidieren.
- **Server akzeptiert clientseitige Mod nicht**: rein clientseitige Mods (Minimap,
  Shader) gehören nicht auf den dedizierten Server.
- **`.mrpack` importiert keine Mods**: Einträge ohne `downloads` werden nicht
  geladen — Mod von Modrinth auflösen oder die `.jar` in `overrides/mods/` legen.

## Performance
- Standard-Performance-Mods (Fabric): **Sodium, Lithium, FerriteCore, Krypton,
  Entity Culling**. Geben oft den größten Schub bei wenig Risiko.
