"""Phase-2-Werkzeuge: Items und Blöcke zu einer bestehenden Fabric-Mod hinzufügen.

Stevi pflegt ein Inhalts-Manifest und regeneriert daraus deterministisch die
Registrierungs-Klassen ``ModItems`` / ``ModBlocks``. Zusätzlich werden Modell-,
Blockstate-, Loot-Table- und Sprachdateien sowie eine Platzhalter-Textur erzeugt
und ein ``initialize()``-Aufruf in die Haupt-Mod-Klasse eingeklinkt.

Hinweis: Die exakten Java-/API-Signaturen sind Minecraft-versionsabhängig (Standard
hier: 1.21.x-Stil). Bei einer anderen Version müssen einzelne Zeilen ggf. angepasst
werden — Stevi weist darauf hin.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import project as P


def _reg_name(name: str) -> str:
    """Registry-Pfad (klein, a-z0-9_), z.B. 'Magic Wand' -> 'magic_wand'."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "thing"


def _const(name: str) -> str:
    return _reg_name(name).upper()


def _resolve(workspace: Path, mod_identifier: str) -> tuple[Path | None, str]:
    project = P.find_project(workspace, mod_identifier)
    if project is None:
        return None, (
            f"Keine Mod '{mod_identifier}' im Workspace gefunden. Lege sie zuerst "
            f"mit create_fabric_mod an, oder prüfe den Namen/die Mod-ID."
        )
    return project, ""


# ---------------------------------------------------------------------------
# Item hinzufügen
# ---------------------------------------------------------------------------


def add_item(tool_input: dict[str, Any], workspace: Path) -> str:
    mod_identifier = tool_input["mod"].strip()
    display = tool_input["name"].strip()
    reg = _reg_name(tool_input.get("item_id") or display)

    project, err = _resolve(workspace, mod_identifier)
    if project is None:
        return err
    meta = P.read_mod_meta(project)
    mod_id, package = meta["mod_id"], meta["package"]

    content = P.load_content(project)
    if any(i["name"] == reg for i in content["items"]):
        return f"Das Item '{reg}' existiert in dieser Mod bereits."
    content["items"].append({"name": reg, "display": display})
    P.save_content(project, content)

    # ModItems-Klasse neu erzeugen.
    P.write_file(
        P.java_file(project, f"{package}.content", "ModItems"),
        _items_class(package, mod_id, content["items"]),
    )
    # Ressourcen: Item-Modell, Sprach-Eintrag, Platzhalter-Textur.
    P.write_file(
        project / f"src/main/resources/assets/{mod_id}/models/item/{reg}.json",
        '{\n  "parent": "item/generated",\n'
        f'  "textures": {{ "layer0": "{mod_id}:item/{reg}" }}\n}}\n',
    )
    P.merge_lang(project, mod_id, {f"item.{mod_id}.{reg}": display})
    P.write_placeholder_texture(
        project / f"src/main/resources/assets/{mod_id}/textures/item/{reg}.png"
    )
    injected = P.ensure_init_call(project, meta, f"{package}.content.ModItems.initialize();")

    return (
        f"✅ Item '{display}' (id: {mod_id}:{reg}) zur Mod '{meta['name']}' hinzugefügt.\n"
        f"   • Registrierung: content/ModItems.java (Konstante {_const(reg)})\n"
        f"   • Modell + Platzhalter-Textur + Sprach-Eintrag angelegt\n"
        f"{'   • initialize()-Aufruf in die Hauptklasse eingefügt' + chr(10) if injected else ''}"
        f"   Tausche die Platzhalter-Textur unter assets/{mod_id}/textures/item/{reg}.png "
        f"gegen dein eigenes 16x16-PNG aus."
    )


def _items_class(package: str, mod_id: str, items: list[dict[str, str]]) -> str:
    fields = "\n".join(
        f'    public static final Item {_const(i["name"])} = register("{i["name"]}");'
        for i in items
    )
    group_adds = "\n".join(
        f"            entries.add({_const(i['name'])});" for i in items
    )
    return f"""\
package {package}.content;

import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroups;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;

/** Von Stevi generiert — registriert die Items dieser Mod. */
public class ModItems {{
    public static final String MOD_ID = "{mod_id}";

{fields}

    private static Item register(String name) {{
        return Registry.register(
            Registries.ITEM, Identifier.of(MOD_ID, name), new Item(new Item.Settings()));
    }}

    public static void initialize() {{
        ItemGroupEvents.modifyEntriesEvent(ItemGroups.INGREDIENTS).register(entries -> {{
{group_adds}
        }});
    }}
}}
"""


# ---------------------------------------------------------------------------
# Block hinzufügen
# ---------------------------------------------------------------------------


def add_block(tool_input: dict[str, Any], workspace: Path) -> str:
    mod_identifier = tool_input["mod"].strip()
    display = tool_input["name"].strip()
    reg = _reg_name(tool_input.get("block_id") or display)

    project, err = _resolve(workspace, mod_identifier)
    if project is None:
        return err
    meta = P.read_mod_meta(project)
    mod_id, package = meta["mod_id"], meta["package"]

    content = P.load_content(project)
    if any(b["name"] == reg for b in content["blocks"]):
        return f"Der Block '{reg}' existiert in dieser Mod bereits."
    content["blocks"].append({"name": reg, "display": display})
    P.save_content(project, content)

    P.write_file(
        P.java_file(project, f"{package}.content", "ModBlocks"),
        _blocks_class(package, mod_id, content["blocks"]),
    )

    res = f"src/main/resources/assets/{mod_id}"
    data = f"src/main/resources/data/{mod_id}"
    # Blockstate
    P.write_file(
        project / f"{res}/blockstates/{reg}.json",
        '{\n  "variants": {\n    "": { "model": '
        f'"{mod_id}:block/{reg}" }}\n  }}\n}}\n',
    )
    # Block-Modell (cube_all)
    P.write_file(
        project / f"{res}/models/block/{reg}.json",
        '{\n  "parent": "block/cube_all",\n'
        f'  "textures": {{ "all": "{mod_id}:block/{reg}" }}\n}}\n',
    )
    # Item-Modell (erbt vom Block-Modell)
    P.write_file(
        project / f"{res}/models/item/{reg}.json",
        f'{{\n  "parent": "{mod_id}:block/{reg}"\n}}\n',
    )
    # Loot-Table (Block droppt sich selbst)
    P.write_file(
        project / f"{data}/loot_table/blocks/{reg}.json",
        _self_drop_loot(mod_id, reg),
    )
    P.merge_lang(project, mod_id, {f"block.{mod_id}.{reg}": display})
    P.write_placeholder_texture(project / f"{res}/textures/block/{reg}.png")
    injected = P.ensure_init_call(project, meta, f"{package}.content.ModBlocks.initialize();")

    return (
        f"✅ Block '{display}' (id: {mod_id}:{reg}) zur Mod '{meta['name']}' hinzugefügt.\n"
        f"   • Registrierung: content/ModBlocks.java (Block + BlockItem)\n"
        f"   • Blockstate, Block-/Item-Modell, Loot-Table, Sprach-Eintrag, Platzhalter-Textur\n"
        f"{'   • initialize()-Aufruf in die Hauptklasse eingefügt' + chr(10) if injected else ''}"
        f"   Tausche die Textur unter assets/{mod_id}/textures/block/{reg}.png aus."
    )


def _blocks_class(package: str, mod_id: str, blocks: list[dict[str, str]]) -> str:
    fields = "\n".join(
        f'    public static final Block {_const(b["name"])} = '
        f'register("{b["name"]}", new Block(AbstractBlock.Settings.create()));'
        for b in blocks
    )
    return f"""\
package {package}.content;

import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;

/** Von Stevi generiert — registriert die Blöcke dieser Mod (inkl. BlockItem). */
public class ModBlocks {{
    public static final String MOD_ID = "{mod_id}";

{fields}

    private static Block register(String name, Block block) {{
        Block registered = Registry.register(
            Registries.BLOCK, Identifier.of(MOD_ID, name), block);
        Registry.register(
            Registries.ITEM, Identifier.of(MOD_ID, name),
            new BlockItem(registered, new Item.Settings()));
        return registered;
    }}

    public static void initialize() {{
        // Blöcke werden bei Klassenladung registriert.
    }}
}}
"""


def add_recipe(tool_input: dict[str, Any], workspace: Path) -> str:
    """Fügt ein Crafting-Rezept (shaped/shapeless) als data-JSON hinzu."""
    project, err = _resolve(workspace, tool_input["mod"].strip())
    if project is None:
        return err
    meta = P.read_mod_meta(project)
    mod_id = meta["mod_id"]

    rtype = (tool_input.get("type") or "shaped").strip().lower()
    result_id = tool_input["result"].strip()
    if ":" not in result_id:
        result_id = f"{mod_id}:{result_id}"
    try:
        count = max(1, int(tool_input.get("count", 1) or 1))
    except (TypeError, ValueError):
        count = 1
    recipe_id = _reg_name(tool_input.get("recipe_id") or result_id.split(":")[-1])

    if rtype.startswith("shapeless"):
        ingredients = tool_input.get("ingredients") or []
        if not ingredients:
            return "Für ein shapeless-Rezept bitte 'ingredients' (Liste von Item-IDs) angeben."
        data: dict[str, Any] = {
            "type": "minecraft:crafting_shapeless",
            "ingredients": [{"item": i} for i in ingredients],
            "result": {"id": result_id, "count": count},
        }
    else:
        pattern = tool_input.get("pattern") or []
        key = tool_input.get("key") or {}
        if not pattern or not key:
            return (
                "Für ein shaped-Rezept bitte 'pattern' (z.B. [\"###\",\" # \",\" # \"]) "
                "und 'key' (z.B. {\"#\": \"minecraft:stick\"}) angeben."
            )
        data = {
            "type": "minecraft:crafting_shaped",
            "pattern": pattern,
            "key": {k: {"item": v} for k, v in key.items()},
            "result": {"id": result_id, "count": count},
        }

    out = project / f"src/main/resources/data/{mod_id}/recipe/{recipe_id}.json"
    P.write_file(out, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return (
        f"✅ Rezept '{recipe_id}' ({rtype}) zur Mod '{meta['name']}' hinzugefügt.\n"
        f"   • Ergebnis: {count}x {result_id}\n"
        f"   • Datei: src/main/resources/data/{mod_id}/recipe/{recipe_id}.json\n"
        f"   Hinweis: In MC 1.21+ liegt das Rezept im Ordner 'recipe' (Einzahl)."
    )


def _self_drop_loot(mod_id: str, reg: str) -> str:
    return (
        "{\n"
        '  "type": "minecraft:block",\n'
        '  "pools": [\n    {\n      "rolls": 1,\n'
        '      "entries": [\n        {\n'
        '          "type": "minecraft:item",\n'
        f'          "name": "{mod_id}:{reg}"\n'
        "        }\n      ]\n    }\n  ]\n}\n"
    )
