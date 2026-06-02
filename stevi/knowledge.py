"""Wissensdatenbank (RAG) für Stevi.

Lädt die Markdown-Dateien unter ``stevi/knowledge/`` und stellt eine einfache
schlagwortbasierte Suche bereit. Das Ergebnis wird Claude als Kontext mitgegeben.

Bewusst leichtgewichtig gehalten: keine externen Vektor-Datenbanken nötig. Die
Suche zerlegt die Dokumente in Abschnitte (nach Markdown-Überschriften) und
bewertet sie nach Begriffs-Überlappung mit der Nutzerfrage. Das reicht für eine
kuratierte, überschaubare Wissensbasis völlig aus und lässt sich später leicht
gegen echtes Embedding-RAG austauschen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# Häufige deutsche/englische Füllwörter, die für die Suche irrelevant sind.
_STOPWORDS = {
    "und", "oder", "der", "die", "das", "ein", "eine", "einen", "wie", "was",
    "ich", "du", "mir", "mit", "für", "von", "den", "dem", "ist", "sind", "soll",
    "kann", "man", "the", "and", "for", "with", "how", "what", "you", "can", "to",
    "a", "an", "of", "in", "is", "it",
}


@dataclass
class Section:
    """Ein Wissens-Abschnitt: Überschrift + Inhalt aus einer Markdown-Datei."""

    source: str       # Dateiname, z.B. "fabric-basics.md"
    heading: str      # Überschrift des Abschnitts
    body: str         # Reiner Textinhalt des Abschnitts

    @property
    def text(self) -> str:
        return f"## {self.heading}\n{self.body}".strip()


def _tokenize(text: str) -> list[str]:
    """Zerlegt Text in kleingeschriebene Wort-Token ohne Füllwörter."""
    words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 2]


def _split_into_sections(source: str, content: str) -> list[Section]:
    """Teilt eine Markdown-Datei an ``#``/``##``-Überschriften in Abschnitte."""
    sections: list[Section] = []
    heading = source
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            sections.append(Section(source=source, heading=heading, body=body))

    for line in content.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)$", line)
        if m:
            flush()
            heading = m.group(1).strip()
            buffer = []
        else:
            buffer.append(line)
    flush()
    return sections


class KnowledgeBase:
    """Lädt und durchsucht die Markdown-Wissensbasis.

    Lädt immer die mitgelieferte (kuratierte) Wissensbasis und zusätzlich beliebige
    ``extra_dirs`` — z.B. das Verzeichnis mit importiertem Wissen (Mod-Code,
    Video-Transkripte). So wächst Stevis Wissen, ohne dass etwas neu trainiert wird.
    """

    def __init__(
        self,
        directory: Path = KNOWLEDGE_DIR,
        extra_dirs: list[Path] | None = None,
    ) -> None:
        self.directories: list[Path] = [directory]
        if extra_dirs:
            self.directories.extend(extra_dirs)
        self.sections: list[Section] = []
        self._load()

    def _load(self) -> None:
        for directory in self.directories:
            if not directory or not Path(directory).is_dir():
                continue
            for path in sorted(Path(directory).glob("*.md")):
                content = path.read_text(encoding="utf-8")
                self.sections.extend(_split_into_sections(path.name, content))

    def search(self, query: str, top_k: int = 3) -> list[Section]:
        """Gibt die ``top_k`` relevantesten Abschnitte zur Frage zurück."""
        query_tokens = set(_tokenize(query))
        if not query_tokens or not self.sections:
            return []

        scored: list[tuple[float, Section]] = []
        for section in self.sections:
            section_tokens = _tokenize(section.text)
            if not section_tokens:
                continue
            section_set = set(section_tokens)
            overlap = query_tokens & section_set
            if not overlap:
                continue
            # Score: Treffer gewichtet, leicht normalisiert über Abschnittslänge,
            # damit sehr lange Abschnitte nicht alles dominieren.
            score = len(overlap) + sum(
                section_tokens.count(t) for t in overlap
            ) / max(len(section_tokens), 1)
            scored.append((score, section))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [section for _, section in scored[:top_k]]

    def context_for(self, query: str, top_k: int = 3) -> str:
        """Baut einen fertigen Kontext-Block für den Prompt — oder leeren String."""
        hits = self.search(query, top_k=top_k)
        if not hits:
            return ""
        parts = [f"[Quelle: {s.source}]\n{s.text}" for s in hits]
        return "\n\n---\n\n".join(parts)
