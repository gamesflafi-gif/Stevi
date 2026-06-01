"""Tests für Phase 2–4: Items/Blöcke, Build, Analyse/Umschreiben, Mixin."""

from __future__ import annotations

import json
from pathlib import Path

from stevi.tools import execute_tool
from stevi.tools.build import resolve_build_command


def _make_mod(workspace: Path, name: str = "Test Mod") -> str:
    execute_tool("create_fabric_mod", {"name": name, "minecraft_version": "1.21.1"}, workspace)
    return name


# ---------------------------------------------------------------------------
# Phase 2 — add_item / add_block
# ---------------------------------------------------------------------------


def test_add_item(tmp_path: Path):
    _make_mod(tmp_path)
    result = execute_tool("add_item", {"mod": "test_mod", "name": "Ruby"}, tmp_path)
    assert "hinzugefügt" in result.lower()

    proj = tmp_path / "test_mod"
    items_java = proj / "src/main/java/net/stevi/test_mod/content/ModItems.java"
    assert items_java.is_file()
    text = items_java.read_text(encoding="utf-8")
    assert 'register("ruby")' in text
    assert "public static final Item RUBY" in text

    # Modell, Textur, Sprache, Manifest
    assert (proj / "src/main/resources/assets/test_mod/models/item/ruby.json").is_file()
    assert (proj / "src/main/resources/assets/test_mod/textures/item/ruby.png").is_file()
    lang = json.loads((proj / "src/main/resources/assets/test_mod/lang/en_us.json").read_text())
    assert lang["item.test_mod.ruby"] == "Ruby"
    manifest = json.loads((proj / ".stevi/content.json").read_text())
    assert manifest["items"][0]["name"] == "ruby"

    # initialize()-Aufruf wurde in die Hauptklasse eingefügt
    main = (proj / "src/main/java/net/stevi/test_mod/TestModMod.java").read_text()
    assert "ModItems.initialize();" in main


def test_add_item_placeholder_png_is_valid(tmp_path: Path):
    _make_mod(tmp_path)
    execute_tool("add_item", {"mod": "test_mod", "name": "Gem"}, tmp_path)
    png = (tmp_path / "test_mod/src/main/resources/assets/test_mod/textures/item/gem.png").read_bytes()
    assert png.startswith(b"\x89PNG\r\n\x1a\n")  # gültige PNG-Signatur


def test_add_two_items_regenerates_class(tmp_path: Path):
    _make_mod(tmp_path)
    execute_tool("add_item", {"mod": "test_mod", "name": "Ruby"}, tmp_path)
    execute_tool("add_item", {"mod": "test_mod", "name": "Sapphire"}, tmp_path)
    text = (tmp_path / "test_mod/src/main/java/net/stevi/test_mod/content/ModItems.java").read_text()
    assert 'register("ruby")' in text and 'register("sapphire")' in text
    # initialize()-Aufruf nur EINMAL eingefügt (idempotent)
    main = (tmp_path / "test_mod/src/main/java/net/stevi/test_mod/TestModMod.java").read_text()
    assert main.count("ModItems.initialize();") == 1


def test_add_item_duplicate(tmp_path: Path):
    _make_mod(tmp_path)
    execute_tool("add_item", {"mod": "test_mod", "name": "Ruby"}, tmp_path)
    again = execute_tool("add_item", {"mod": "test_mod", "name": "ruby"}, tmp_path)
    assert "bereits" in again.lower()


def test_add_item_missing_mod(tmp_path: Path):
    result = execute_tool("add_item", {"mod": "gibtsnicht", "name": "X"}, tmp_path)
    assert "keine mod" in result.lower()


def test_add_block(tmp_path: Path):
    _make_mod(tmp_path)
    result = execute_tool("add_block", {"mod": "test_mod", "name": "Ruby Ore"}, tmp_path)
    assert "hinzugefügt" in result.lower()
    proj = tmp_path / "test_mod"
    blocks_java = (proj / "src/main/java/net/stevi/test_mod/content/ModBlocks.java").read_text()
    assert 'register("ruby_ore"' in blocks_java
    assert "BlockItem" in blocks_java
    assert (proj / "src/main/resources/assets/test_mod/blockstates/ruby_ore.json").is_file()
    assert (proj / "src/main/resources/assets/test_mod/models/block/ruby_ore.json").is_file()
    assert (proj / "src/main/resources/data/test_mod/loot_table/blocks/ruby_ore.json").is_file()


# ---------------------------------------------------------------------------
# Phase 3 — build_mod
# ---------------------------------------------------------------------------


def test_build_mod_missing_project(tmp_path: Path):
    assert "keine mod" in execute_tool("build_mod", {"mod": "nix"}, tmp_path).lower()


def test_resolve_build_command_prefers_wrapper(tmp_path: Path):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
    cmd, err = resolve_build_command(proj)
    assert err == ""
    assert cmd is not None and cmd[0].endswith("gradlew")
    assert "build" in cmd


def test_build_mod_without_gradle(tmp_path: Path, monkeypatch):
    _make_mod(tmp_path)
    # Kein Wrapper im generierten Projekt + 'gradle' nicht auffindbar simulieren.
    monkeypatch.setattr("stevi.tools.build.shutil.which", lambda _x: None)
    result = execute_tool("build_mod", {"mod": "test_mod"}, tmp_path)
    assert "gradle" in result.lower()


# ---------------------------------------------------------------------------
# Phase 4 — analyze / read / write / mixin
# ---------------------------------------------------------------------------


def test_analyze_mod(tmp_path: Path):
    _make_mod(tmp_path)
    execute_tool("add_item", {"mod": "test_mod", "name": "Ruby"}, tmp_path)
    result = execute_tool("analyze_mod", {"mod": "test_mod"}, tmp_path)
    assert "test_mod" in result
    assert "ruby" in result.lower()


def test_read_and_write_mod_file(tmp_path: Path):
    _make_mod(tmp_path)
    read = execute_tool(
        "read_mod_file",
        {"mod": "test_mod", "path": "src/main/resources/fabric.mod.json"},
        tmp_path,
    )
    assert "test_mod" in read

    write = execute_tool(
        "write_mod_file",
        {"mod": "test_mod", "path": "src/main/resources/notiz.txt", "content": "Hallo Stevi"},
        tmp_path,
    )
    assert "geschrieben" in write.lower()
    assert (tmp_path / "test_mod/src/main/resources/notiz.txt").read_text() == "Hallo Stevi"


def test_write_mod_file_blocks_traversal(tmp_path: Path):
    _make_mod(tmp_path)
    result = execute_tool(
        "write_mod_file",
        {"mod": "test_mod", "path": "../../evil.txt", "content": "x"},
        tmp_path,
    )
    assert "ungültiger pfad" in result.lower()
    assert not (tmp_path / "evil.txt").exists()


def test_add_mixin_client(tmp_path: Path):
    _make_mod(tmp_path)
    result = execute_tool(
        "add_mixin",
        {"mod": "test_mod", "target_class": "net.minecraft.client.MinecraftClient"},
        tmp_path,
    )
    assert "mixin" in result.lower()
    proj = tmp_path / "test_mod"
    mixin_file = proj / "src/main/java/net/stevi/test_mod/mixin/client/MinecraftClientMixin.java"
    assert mixin_file.is_file()
    assert "@Mixin(MinecraftClient.class)" in mixin_file.read_text()
    cfg = json.loads((proj / "src/main/resources/test_mod.mixins.json").read_text())
    assert "client.MinecraftClientMixin" in cfg["client"]
