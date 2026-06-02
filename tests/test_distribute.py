"""Tests für Phase 5: Modrinth-Auflösung, .mrpack-Export, Validierung."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from stevi.tools import distribute, execute_tool


def _make_pack(workspace: Path, name: str = "Mein Pack") -> str:
    execute_tool(
        "create_modpack",
        {"name": name, "minecraft_version": "1.21.1", "loader": "fabric"},
        workspace,
    )
    return name


# ---------------------------------------------------------------------------
# add_mod_from_modrinth (mit gemocktem HTTP)
# ---------------------------------------------------------------------------


def test_add_mod_from_modrinth(tmp_path: Path, monkeypatch):
    _make_pack(tmp_path)

    def fake_get_json(url: str):
        if "/search" in url:
            return {"hits": [{"slug": "sodium", "title": "Sodium"}]}
        if "/version" in url:
            return [
                {
                    "version_number": "0.5.8",
                    "files": [
                        {
                            "primary": True,
                            "filename": "sodium-fabric-0.5.8.jar",
                            "url": "https://cdn.modrinth.com/data/AANobbMI/sodium.jar",
                            "size": 123456,
                            "hashes": {"sha1": "abc", "sha512": "def"},
                        }
                    ],
                }
            ]
        raise AssertionError(f"Unerwartete URL: {url}")

    monkeypatch.setattr(distribute, "_get_json", fake_get_json)

    result = execute_tool(
        "add_mod_from_modrinth", {"modpack_name": "Mein Pack", "mod": "sodium"}, tmp_path
    )
    assert "hinzugefügt" in result.lower()

    manifest = json.loads((tmp_path / "mein-pack/modrinth.index.json").read_text())
    entry = manifest["files"][0]
    assert entry["path"] == "mods/sodium-fabric-0.5.8.jar"
    assert entry["downloads"] == ["https://cdn.modrinth.com/data/AANobbMI/sodium.jar"]
    assert entry["hashes"] == {"sha1": "abc", "sha512": "def"}
    assert entry["fileSize"] == 123456


def test_add_mod_from_modrinth_resolves_dependencies(tmp_path: Path, monkeypatch):
    _make_pack(tmp_path)

    def fake_get_json(url: str):
        if "/search" in url:
            return {"hits": [{"slug": "create", "title": "Create"}]}
        if "/version/DEPVER" in url:  # Abhängigkeit per version_id
            return {
                "version_number": "1.0",
                "files": [
                    {"primary": True, "filename": "flywheel.jar",
                     "url": "https://cdn/flywheel.jar", "size": 10, "hashes": {}}
                ],
            }
        if "/version" in url:  # Hauptmod
            return [
                {
                    "version_number": "0.5",
                    "dependencies": [
                        {"dependency_type": "required", "version_id": "DEPVER",
                         "file_name": "flywheel.jar"},
                        {"dependency_type": "optional", "project_id": "ignored"},
                    ],
                    "files": [
                        {"primary": True, "filename": "create.jar",
                         "url": "https://cdn/create.jar", "size": 20, "hashes": {}}
                    ],
                }
            ]
        raise AssertionError(f"Unerwartete URL: {url}")

    monkeypatch.setattr(distribute, "_get_json", fake_get_json)
    result = execute_tool(
        "add_mod_from_modrinth", {"modpack_name": "Mein Pack", "mod": "create"}, tmp_path
    )
    assert "aufgelöst" in result.lower()
    manifest = json.loads((tmp_path / "mein-pack/modrinth.index.json").read_text())
    paths = {f["path"] for f in manifest["files"]}
    assert "mods/create.jar" in paths
    assert "mods/flywheel.jar" in paths  # required-Abhängigkeit mit aufgenommen


def test_search_modrinth(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        distribute,
        "_get_json",
        lambda url: {"hits": [
            {"title": "Sodium", "slug": "sodium", "downloads": 5000000,
             "description": "Rendering-Optimierung"},
        ]},
    )
    result = execute_tool("search_modrinth", {"query": "performance"}, tmp_path)
    assert "sodium" in result.lower()
    assert "5,000,000" in result


def test_add_mod_from_modrinth_not_found(tmp_path: Path, monkeypatch):
    _make_pack(tmp_path)
    monkeypatch.setattr(distribute, "_get_json", lambda url: {"hits": []})
    result = execute_tool(
        "add_mod_from_modrinth", {"modpack_name": "Mein Pack", "mod": "gibtsnicht"}, tmp_path
    )
    assert "kein mod" in result.lower()


def test_add_mod_from_modrinth_no_pack(tmp_path: Path):
    result = execute_tool(
        "add_mod_from_modrinth", {"modpack_name": "Nada", "mod": "sodium"}, tmp_path
    )
    assert "kein modpack" in result.lower()


# ---------------------------------------------------------------------------
# export_modpack
# ---------------------------------------------------------------------------


def test_export_modpack(tmp_path: Path):
    _make_pack(tmp_path)
    # Ein Mod mit Download-Quelle ...
    execute_tool(
        "add_mod_to_modpack",
        {"modpack_name": "Mein Pack", "mod_name": "Sodium", "download_url": "https://x/sodium.jar"},
        tmp_path,
    )
    # ... und eine Override-Datei.
    overrides = tmp_path / "mein-pack/overrides/config"
    overrides.mkdir(parents=True, exist_ok=True)
    (overrides / "test.toml").write_text("a=1", encoding="utf-8")

    result = execute_tool("export_modpack", {"name": "Mein Pack"}, tmp_path)
    assert "exportiert" in result.lower()

    mrpack = tmp_path / "mein-pack.mrpack"
    assert mrpack.is_file()
    with zipfile.ZipFile(mrpack) as zf:
        names = zf.namelist()
        assert "modrinth.index.json" in names
        assert "overrides/config/test.toml" in names
        index = json.loads(zf.read("modrinth.index.json"))
    # Internes "_name" darf NICHT im exportierten Index stehen.
    assert index["files"]
    assert all("_name" not in f for f in index["files"])
    assert index["files"][0]["downloads"] == ["https://x/sodium.jar"]


def test_export_warns_about_mods_without_download(tmp_path: Path):
    _make_pack(tmp_path)
    execute_tool(
        "add_mod_to_modpack", {"modpack_name": "Mein Pack", "mod_name": "OhneURL"}, tmp_path
    )
    result = execute_tool("export_modpack", {"name": "Mein Pack"}, tmp_path)
    assert "ohne download" in result.lower()
    # Mod ohne Download wird nicht in den Index aufgenommen.
    with zipfile.ZipFile(tmp_path / "mein-pack.mrpack") as zf:
        index = json.loads(zf.read("modrinth.index.json"))
    assert index["files"] == []


# ---------------------------------------------------------------------------
# validate_modpack
# ---------------------------------------------------------------------------


def test_validate_modpack_clean(tmp_path: Path):
    _make_pack(tmp_path)
    execute_tool(
        "add_mod_to_modpack",
        {"modpack_name": "Mein Pack", "mod_name": "Sodium", "download_url": "https://x/s.jar"},
        tmp_path,
    )
    result = execute_tool("validate_modpack", {"name": "Mein Pack"}, tmp_path)
    assert "keine probleme" in result.lower()


def test_validate_modpack_warns_missing_download(tmp_path: Path):
    _make_pack(tmp_path)
    execute_tool("add_mod_to_modpack", {"modpack_name": "Mein Pack", "mod_name": "X"}, tmp_path)
    result = execute_tool("validate_modpack", {"name": "Mein Pack"}, tmp_path)
    assert "ohne download" in result.lower()


def test_validate_modpack_missing(tmp_path: Path):
    assert "kein modpack" in execute_tool("validate_modpack", {"name": "Nix"}, tmp_path).lower()
