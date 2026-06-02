# Modpack-Grundlagen

## Was ist ein Modpack?
Ein Modpack ist eine zusammengestellte Sammlung von Mods (plus Konfigurationen,
Ressourcenpaketen und manchmal Welten), die zusammen ein bestimmtes Spielerlebnis
ergeben. Alle Mods müssen für **dieselbe Minecraft-Version** und denselben
**Loader** (Fabric/Forge/NeoForge/Quilt) gebaut sein.

## Die wichtigsten Bausteine
- **Minecraft-Version**: z.B. 1.21.1. Bestimmt, welche Mods kompatibel sind.
- **Mod-Loader**: Fabric, Forge, NeoForge oder Quilt. Mods für Fabric laufen NICHT
  unter Forge und umgekehrt.
- **Mods**: einzelne `.jar`-Dateien im `mods/`-Ordner.
- **Configs**: Einstellungen einzelner Mods unter `config/`.
- **Abhängigkeiten**: viele Mods brauchen die **Fabric API** oder eine Bibliotheks-Mod.

## Verteilformate
- **Modrinth (`.mrpack`)**: ein ZIP mit `modrinth.index.json` (Liste der Mods mit
  Download-URLs und Hashes) plus einem `overrides/`-Ordner für eigene Configs/Mods.
  Offen, gut dokumentiert, vom Modrinth-App und Prism Launcher unterstützt.
- **CurseForge**: eigenes `manifest.json`-Format, über den CurseForge/Overwolf-App.
- **MultiMC / Prism Launcher Instanz**: lokaler Ordner mit `mods/`, `config/` usw.

## Aufbau eines Modrinth-Manifests (`modrinth.index.json`)
```json
{
  "formatVersion": 1,
  "game": "minecraft",
  "versionId": "1.0.0",
  "name": "Mein Abenteuer-Pack",
  "files": [
    {
      "path": "mods/sodium.jar",
      "downloads": ["https://cdn.modrinth.com/.../sodium.jar"],
      "env": { "client": "required", "server": "unsupported" }
    }
  ],
  "dependencies": {
    "minecraft": "1.21.1",
    "fabric-loader": "0.16.5"
  }
}
```
- `files`: jede Mod mit Pfad, Download-Link und (optional) Hashes.
- `env`: ob eine Mod auf Client/Server nötig ist (`required`/`optional`/`unsupported`).
- `dependencies`: Minecraft-Version + Loader-Version.
- `overrides/`: alles in diesem Ordner wird direkt in die Instanz kopiert (eigene
  Configs, Mods ohne Download-URL).

## Ein gutes Modpack zusammenstellen — Reihenfolge
1. **Version & Loader festlegen** (z.B. Fabric 1.21.1).
2. **Basis/Performance**: Fabric API, Sodium, Lithium, FerriteCore.
3. **Inhalts-Mods**: die Mods, die das Thema ausmachen (z.B. Magie, Tech, Bauen).
4. **Abhängigkeiten prüfen**: jede Mod-Beschreibung nennt benötigte Bibliotheken.
5. **Konflikte vermeiden**: keine zwei Mods, die dasselbe tun (z.B. nicht Sodium UND
   OptiFine). Auf passende Minecraft-Version aller Mods achten.
6. **Testen**: Instanz starten, Log auf Fehler prüfen, Mods bei Crashes einzeln
   eingrenzen.

## Häufige Stolperfallen
- **Loader-Mischmasch**: Fabric- und Forge-Mods im selben Pack → funktioniert nicht.
- **Falsche Minecraft-Version**: eine 1.20.1-Mod in einem 1.21.1-Pack lädt nicht.
- **Fehlende Fabric API**: viele Fabric-Mods stürzen ohne sie ab.
- **Client-/Server-Mods**: rein clientseitige Mods (z.B. Minimap) gehören nicht auf
  einen dedizierten Server.

## Performance-Mods (Fabric), fast immer sinnvoll
- **Sodium** (Rendering), **Lithium** (Spiel-Logik), **FerriteCore** (RAM),
  **Krypton** (Netzwerk), **Entity Culling** (weniger unsichtbare Entities rendern).
