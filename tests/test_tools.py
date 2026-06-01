"""Tests für Stevis Werkzeuge und Wissensdatenbank — laufen ohne API-Schlüssel."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from stevi.knowledge import KnowledgeBase
from stevi.tools import execute_tool
from stevi.tools.fabric_mod import pascal_case, slugify_mod_id


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def test_slugify_mod_id():
    assert slugify_mod_id("Magic Wands") == "magic_wands"
    assert slugify_mod_id("  Cool!!Mod  ") == "cool_mod"
    assert slugify_mod_id("123 Pack") == "mod_123_pack"
    assert slugify_mod_id("") == "stevi_mod"


def test_pascal_case():
    assert pascal_case("magic wands") == "MagicWands"
    assert pascal_case("cool-mod_42") == "CoolMod42"
    assert pascal_case("") == "SteviMod"


# ---------------------------------------------------------------------------
# Fabric-Mod erstellen
# ---------------------------------------------------------------------------


def test_create_fabric_mod_creates_project(tmp_path: Path):
    result = execute_tool(
        "create_fabric_mod",
        {"name": "Magic Wands", "minecraft_version": "1.21.1"},
        tmp_path,
    )
    assert "Magic Wands" in result

    project = tmp_path / "magic_wands"
    assert (project / "build.gradle").is_file()
    assert (project / "gradle.properties").is_file()
    assert (project / "settings.gradle").is_file()

    fabric_json = project / "src/main/resources/fabric.mod.json"
    assert fabric_json.is_file()
    data = json.loads(fabric_json.read_text(encoding="utf-8"))
    assert data["id"] == "magic_wands"
    assert data["name"] == "Magic Wands"
    assert data["entrypoints"]["main"] == ["net.stevi.magic_wands.MagicWandsMod"]

    # Haupt-Klasse liegt am erwarteten Package-Pfad.
    main_class = project / "src/main/java/net/stevi/magic_wands/MagicWandsMod.java"
    assert main_class.is_file()
    assert "implements ModInitializer" in main_class.read_text(encoding="utf-8")


def test_create_fabric_mod_custom_package(tmp_path: Path):
    execute_tool(
        "create_fabric_mod",
        {"name": "Tech Stuff", "package": "com.example.tech", "mod_id": "techstuff"},
        tmp_path,
    )
    cls = tmp_path / "techstuff/src/main/java/com/example/tech/TechStuffMod.java"
    assert cls.is_file()
    assert "package com.example.tech;" in cls.read_text(encoding="utf-8")


def test_create_fabric_mod_twice_is_safe(tmp_path: Path):
    execute_tool("create_fabric_mod", {"name": "Dup"}, tmp_path)
    second = execute_tool("create_fabric_mod", {"name": "Dup"}, tmp_path)
    assert "existiert bereits" in second.lower()


# ---------------------------------------------------------------------------
# Modpack erstellen / Mods hinzufügen
# ---------------------------------------------------------------------------


def test_create_modpack_and_add_mod(tmp_path: Path):
    execute_tool(
        "create_modpack",
        {"name": "Stevis Abenteuer", "minecraft_version": "1.21.1", "loader": "fabric"},
        tmp_path,
    )
    manifest = tmp_path / "stevis-abenteuer/modrinth.index.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["name"] == "Stevis Abenteuer"
    assert data["dependencies"]["minecraft"] == "1.21.1"
    assert "fabric-loader" in data["dependencies"]
    assert data["files"] == []

    # Mod hinzufügen
    execute_tool(
        "add_mod_to_modpack",
        {"modpack_name": "Stevis Abenteuer", "mod_name": "Sodium",
         "download_url": "https://example.com/sodium.jar"},
        tmp_path,
    )
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert len(data["files"]) == 1
    assert data["files"][0]["_name"] == "Sodium"
    assert data["files"][0]["downloads"] == ["https://example.com/sodium.jar"]


def test_add_mod_avoids_duplicates(tmp_path: Path):
    execute_tool("create_modpack", {"name": "Pack"}, tmp_path)
    execute_tool("add_mod_to_modpack", {"modpack_name": "Pack", "mod_name": "Sodium"}, tmp_path)
    again = execute_tool(
        "add_mod_to_modpack", {"modpack_name": "Pack", "mod_name": "sodium"}, tmp_path
    )
    assert "bereits" in again.lower()


def test_add_mod_to_missing_modpack(tmp_path: Path):
    result = execute_tool(
        "add_mod_to_modpack", {"modpack_name": "Gibtsnicht", "mod_name": "X"}, tmp_path
    )
    assert "kein modpack" in result.lower()


def test_create_modpack_invalid_loader(tmp_path: Path):
    result = execute_tool("create_modpack", {"name": "P", "loader": "banana"}, tmp_path)
    assert "unbekannter loader" in result.lower()


# ---------------------------------------------------------------------------
# list_workspace & unbekanntes Werkzeug
# ---------------------------------------------------------------------------


def test_list_workspace(tmp_path: Path):
    empty = execute_tool("list_workspace", {}, tmp_path)
    assert "leer" in empty.lower()
    execute_tool("create_modpack", {"name": "Pack"}, tmp_path)
    listed = execute_tool("list_workspace", {}, tmp_path)
    assert "pack" in listed.lower()


def test_unknown_tool(tmp_path: Path):
    assert "unbekannt" in execute_tool("does_not_exist", {}, tmp_path).lower()


# ---------------------------------------------------------------------------
# Wissensdatenbank
# ---------------------------------------------------------------------------


def test_knowledge_base_loads_sections():
    kb = KnowledgeBase()
    assert len(kb.sections) > 0


def test_knowledge_search_finds_relevant_section():
    kb = KnowledgeBase()
    hits = kb.search("Wie registriere ich ein Item in Fabric?", top_k=3)
    assert hits
    combined = " ".join(h.text.lower() for h in hits)
    assert "item" in combined


def test_knowledge_context_for_modpack():
    kb = KnowledgeBase()
    context = kb.context_for("Wie baue ich ein Modpack mit Sodium?")
    assert "modpack" in context.lower()


def test_knowledge_search_empty_query():
    kb = KnowledgeBase()
    assert kb.search("", top_k=3) == []
