"""Tests für den Wissens-Importer (Phase 2) — ohne Netzwerk."""

from __future__ import annotations

from pathlib import Path

from stevi.knowledge import KnowledgeBase
from stevi.knowledge_import import (
    clean_transcript,
    import_mod_source,
    import_transcript,
    list_imports,
    slugify,
)


def test_slugify():
    assert slugify("Coole Mod!") == "coole-mod"
    assert slugify("") == "import"


def test_import_mod_source_from_directory(tmp_path: Path):
    # Eine kleine Fake-Mod anlegen.
    src = tmp_path / "mymod"
    (src / "src/main/java/com/x").mkdir(parents=True)
    (src / "src/main/java/com/x/MyMod.java").write_text(
        "public class MyMod { void foo() { System.out.println(\"hi\"); } }",
        encoding="utf-8",
    )
    (src / "src/main/resources").mkdir(parents=True)
    (src / "src/main/resources/fabric.mod.json").write_text(
        '{"id":"mymod","name":"My Mod"}', encoding="utf-8"
    )
    # Dateien, die übersprungen werden müssen:
    (src / "build").mkdir()
    (src / "build/ignored.java").write_text("class Ignored {}", encoding="utf-8")
    (src / "readme.txt").write_text("kein code", encoding="utf-8")

    kb_dir = tmp_path / "knowledge_data"
    result = import_mod_source(str(src), kb_dir, name="My Mod")
    assert "importiert" in result.lower()

    out = kb_dir / "imported-mod-my-mod.md"
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "MyMod.java" in text
    assert "fabric.mod.json" in text
    assert "MyMod" in text
    # build/ und .txt wurden NICHT aufgenommen.
    assert "Ignored" not in text
    assert "kein code" not in text


def test_import_mod_source_missing_dir(tmp_path: Path):
    result = import_mod_source(str(tmp_path / "gibtsnicht"), tmp_path / "kb")
    assert "nicht gefunden" in result.lower()


def test_clean_transcript_srt():
    srt = (
        "1\n"
        "00:00:01,000 --> 00:00:03,000\n"
        "Willkommen zum Tutorial\n"
        "\n"
        "2\n"
        "00:00:03,000 --> 00:00:05,000\n"
        "Willkommen zum Tutorial\n"   # Duplikat
        "\n"
        "3\n"
        "00:00:05,000 --> 00:00:07,000\n"
        "Wir bauen ein Item\n"
    )
    cleaned = clean_transcript(srt)
    assert "Willkommen zum Tutorial" in cleaned
    assert "Wir bauen ein Item" in cleaned
    assert "-->" not in cleaned
    # Duplikat wurde entfernt → nur einmal.
    assert cleaned.count("Willkommen zum Tutorial") == 1


def test_clean_transcript_vtt_tags():
    vtt = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:03.000\n"
        "<c>Hallo</c> <00:00:02.000>Welt\n"
    )
    cleaned = clean_transcript(vtt)
    assert "WEBVTT" not in cleaned
    assert "<c>" not in cleaned
    assert "Hallo" in cleaned and "Welt" in cleaned


def test_import_transcript_and_knowledge_pickup(tmp_path: Path):
    transcript = tmp_path / "tut.srt"
    transcript.write_text(
        "1\n00:00:01,000 --> 00:00:03,000\nSo registrierst du ein Item in Fabric\n",
        encoding="utf-8",
    )
    kb_dir = tmp_path / "knowledge_data"
    result = import_transcript(str(transcript), kb_dir, title="Fabric Items")
    assert "importiert" in result.lower()
    assert (kb_dir / "transcript-fabric-items.md").is_file()

    # Die KnowledgeBase findet das importierte Wissen über extra_dirs.
    kb = KnowledgeBase(extra_dirs=[kb_dir])
    hits = kb.search("Item registrieren Fabric", top_k=5)
    combined = " ".join(h.text.lower() for h in hits)
    assert "fabric" in combined


def test_list_imports(tmp_path: Path):
    kb_dir = tmp_path / "kb"
    assert "kein eigenes wissen" in list_imports(kb_dir).lower()
    kb_dir.mkdir()
    (kb_dir / "transcript-x.md").write_text("# x\nhallo", encoding="utf-8")
    listed = list_imports(kb_dir)
    assert "transcript-x.md" in listed
