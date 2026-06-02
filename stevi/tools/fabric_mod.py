"""Werkzeug: Ein komplettes Fabric-Mod-Gradle-Projekt erzeugen.

Erstellt ein lauffähiges Projektgerüst, das man mit ``./gradlew build`` bauen und
in eine Minecraft-Fabric-Instanz legen kann. Die Versionsnummern in
``gradle.properties`` sollten ggf. an die jeweils aktuelle Fabric-Version
angepasst werden (siehe https://fabricmc.net/develop).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Vernünftige Standard-Versionen. Stevi weist den Nutzer darauf hin, dass diese
# in gradle.properties an die jeweils aktuelle Fabric-Version angepasst werden
# können. Diese Defaults bilden eine gängige, gut dokumentierte Kombination ab.
DEFAULT_MC_VERSION = "1.21.1"
DEFAULT_YARN_MAPPINGS = "1.21.1+build.3"
DEFAULT_LOADER_VERSION = "0.16.5"
DEFAULT_FABRIC_API_VERSION = "0.103.0+1.21.1"
DEFAULT_GRADLE_VERSION = "8.8"


def slugify_mod_id(name: str) -> str:
    """Wandelt einen Anzeigenamen in eine gültige Mod-ID um (a-z, 0-9, _)."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not slug:
        slug = "stevi_mod"
    if slug[0].isdigit():
        slug = f"mod_{slug}"
    return slug


def pascal_case(name: str) -> str:
    """Wandelt einen Namen in PascalCase um, z.B. 'magic wands' -> 'MagicWands'."""
    parts = re.findall(r"[a-zA-Z0-9]+", name)
    pascal = "".join(p.capitalize() for p in parts)
    return pascal or "SteviMod"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_fabric_mod(tool_input: dict[str, Any], workspace: Path) -> str:
    """Legt das Fabric-Mod-Projekt an und gibt eine Zusammenfassung zurück."""
    name: str = tool_input["name"].strip()
    mod_id: str = (tool_input.get("mod_id") or "").strip() or slugify_mod_id(name)
    mod_id = slugify_mod_id(mod_id)  # erneut säubern, falls Nutzer Ungültiges schickt
    package: str = (tool_input.get("package") or "").strip() or f"net.stevi.{mod_id}"
    mc_version: str = (tool_input.get("minecraft_version") or "").strip() or DEFAULT_MC_VERSION
    description: str = (tool_input.get("description") or "").strip() or f"{name} — eine mit Stevi erstellte Fabric-Mod."
    author: str = (tool_input.get("author") or "").strip() or "Unbekannt"

    main_class = f"{pascal_case(name)}Mod"
    client_class = f"{pascal_case(name)}ClientMod"
    package_path = package.replace(".", "/")

    project_dir = workspace / mod_id
    if project_dir.exists():
        return (
            f"Es existiert bereits ein Projekt unter '{project_dir}'. "
            f"Wähle eine andere Mod-ID oder lösche den Ordner zuerst."
        )

    # ---- gradle.properties -------------------------------------------------
    _write(
        project_dir / "gradle.properties",
        _GRADLE_PROPERTIES.format(
            mc_version=mc_version,
            yarn=DEFAULT_YARN_MAPPINGS,
            loader=DEFAULT_LOADER_VERSION,
            fabric_api=DEFAULT_FABRIC_API_VERSION,
            mod_version="1.0.0",
            maven_group=package,
            archives_base=mod_id,
        ),
    )

    # ---- settings.gradle ---------------------------------------------------
    _write(project_dir / "settings.gradle", _SETTINGS_GRADLE)

    # ---- build.gradle ------------------------------------------------------
    _write(project_dir / "build.gradle", _BUILD_GRADLE)

    # ---- fabric.mod.json ---------------------------------------------------
    fabric_mod_json = _build_fabric_mod_json(
        mod_id=mod_id,
        name=name,
        description=description,
        author=author,
        package=package,
        main_class=main_class,
        client_class=client_class,
    )
    _write(project_dir / "src/main/resources/fabric.mod.json", fabric_mod_json)

    # ---- Mixin-Config ------------------------------------------------------
    _write(
        project_dir / f"src/main/resources/{mod_id}.mixins.json",
        _MIXINS_JSON.format(package=package, mc_version=mc_version),
    )

    # ---- Haupt-Mod-Klasse (gemeinsame Seite) -------------------------------
    _write(
        project_dir / f"src/main/java/{package_path}/{main_class}.java",
        _MAIN_CLASS.format(
            package=package,
            main_class=main_class,
            mod_id=mod_id,
            name=name,
        ),
    )

    # ---- Client-Mod-Klasse (clientseitig) ----------------------------------
    _write(
        project_dir / f"src/client/java/{package_path}/{client_class}.java",
        _CLIENT_CLASS.format(
            package=package,
            client_class=client_class,
            mod_id=mod_id,
        ),
    )

    # ---- Sprachdatei (en_us) ----------------------------------------------
    _write(
        project_dir / f"src/main/resources/assets/{mod_id}/lang/en_us.json",
        json.dumps({f"text.{mod_id}.hello": f"Hello from {name}!"}, indent=2) + "\n",
    )

    # ---- Hilfsdateien ------------------------------------------------------
    _write(project_dir / ".gitignore", _MOD_GITIGNORE)
    _write(
        project_dir / "README.md",
        _MOD_README.format(name=name, mod_id=mod_id, mc_version=mc_version, main_class=main_class),
    )

    rel = project_dir
    return (
        f"✅ Fabric-Mod '{name}' wurde angelegt unter:\n  {rel}\n\n"
        f"Wichtige Dateien:\n"
        f"  • src/main/java/{package_path}/{main_class}.java  ← hier kommt deine Logik rein\n"
        f"  • src/main/resources/fabric.mod.json              ← Metadaten der Mod\n"
        f"  • gradle.properties                               ← Minecraft-/Fabric-Versionen\n\n"
        f"Gebaut wird mit:  cd {rel.name} && ./gradlew build\n"
        f"(Beim ersten Mal ggf. 'gradle wrapper' ausführen, um den Gradle-Wrapper zu erzeugen.)\n\n"
        f"Hinweis: Die Versionen (Minecraft {mc_version}, Fabric Loader, Yarn, Fabric API) in "
        f"gradle.properties bei Bedarf an https://fabricmc.net/develop anpassen."
    )


def _build_fabric_mod_json(
    *,
    mod_id: str,
    name: str,
    description: str,
    author: str,
    package: str,
    main_class: str,
    client_class: str,
) -> str:
    data = {
        "schemaVersion": 1,
        "id": mod_id,
        "version": "${version}",
        "name": name,
        "description": description,
        "authors": [author],
        "contact": {},
        "license": "MIT",
        "icon": f"assets/{mod_id}/icon.png",
        "environment": "*",
        "entrypoints": {
            "main": [f"{package}.{main_class}"],
            "client": [f"{package}.{client_class}"],
        },
        "mixins": [f"{mod_id}.mixins.json"],
        "depends": {
            "fabricloader": ">=0.16.0",
            "minecraft": "*",
            "java": ">=21",
            "fabric-api": "*",
        },
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Datei-Vorlagen
# ---------------------------------------------------------------------------

_GRADLE_PROPERTIES = """\
# Done to increase the memory available to gradle.
org.gradle.jvmargs=-Xmx2G
org.gradle.parallel=true

# Fabric Properties
# check these on https://fabricmc.net/develop
minecraft_version={mc_version}
yarn_mappings={yarn}
loader_version={loader}
fabric_version={fabric_api}

# Mod Properties
mod_version={mod_version}
maven_group={maven_group}
archives_base_name={archives_base}
"""

_SETTINGS_GRADLE = """\
pluginManagement {
    repositories {
        maven { url = "https://maven.fabricmc.net/" }
        gradlePluginPortal()
    }
}
"""

_BUILD_GRADLE = """\
plugins {
    id 'fabric-loom' version '1.7-SNAPSHOT'
    id 'maven-publish'
}

version = project.mod_version
group = project.maven_group

base {
    archivesName = project.archives_base_name
}

repositories {
    // Add repositories to retrieve artifacts from in here.
}

dependencies {
    minecraft "com.mojang:minecraft:${project.minecraft_version}"
    mappings "net.fabricmc:yarn:${project.yarn_mappings}:v2"
    modImplementation "net.fabricmc:fabric-loader:${project.loader_version}"
    modImplementation "net.fabricmc.fabric-api:fabric-api:${project.fabric_version}"
}

loom {
    splitEnvironmentSourceSets()

    mods {
        register(project.archives_base_name) {
            sourceSet sourceSets.main
            sourceSet sourceSets.client
        }
    }
}

processResources {
    inputs.property "version", project.version

    filesMatching("fabric.mod.json") {
        expand "version": project.version
    }
}

tasks.withType(JavaCompile).configureEach {
    it.options.release = 21
}

java {
    withSourcesJar()
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

jar {
    from("LICENSE") {
        rename { "${it}_${project.archivesName.get()}" }
    }
}
"""

_MIXINS_JSON = """\
{{
  "required": true,
  "package": "{package}.mixin",
  "compatibilityLevel": "JAVA_21",
  "mixins": [],
  "client": [],
  "injectors": {{
    "defaultRequire": 1
  }}
}}
"""

_MAIN_CLASS = """\
package {package};

import net.fabricmc.api.ModInitializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class {main_class} implements ModInitializer {{
    public static final String MOD_ID = "{mod_id}";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {{
        // Dieser Code läuft, sobald Minecraft auf gemeinsamer (common) Seite ladet.
        // Hier registrierst du Items, Blöcke, Entities, Rezepte usw.
        LOGGER.info("{name} wurde geladen! Viel Spaß beim Modden mit Stevi.");
    }}
}}
"""

_CLIENT_CLASS = """\
package {package};

import net.fabricmc.api.ClientModInitializer;

public class {client_class} implements ClientModInitializer {{
    @Override
    public void onInitializeClient() {{
        // Dieser Code läuft nur auf der Client-Seite (Rendering, Keybindings, GUIs).
    }}
}}
"""

_MOD_GITIGNORE = """\
# Gradle
.gradle/
build/
out/

# Fabric Loom
run/
.fabric/

# IDE
.idea/
*.iml
.vscode/
.settings/
bin/
"""

_MOD_README = """\
# {name}

Eine Fabric-Mod für Minecraft {mc_version}, erstellt mit Stevi.

## Bauen

```bash
./gradlew build
```

Die fertige `.jar` liegt danach in `build/libs/`. Lege sie in den `mods/`-Ordner
einer Fabric-Instanz mit Minecraft {mc_version} und der Fabric API.

## Wo geht's los?

Deine Logik kommt in die Haupt-Klasse `{main_class}` (Methode `onInitialize`).

## Versionen anpassen

Die Minecraft-/Fabric-Versionen stehen in `gradle.properties`. Aktuelle Werte
findest du auf https://fabricmc.net/develop.
"""
