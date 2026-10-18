"""Тесты парсера .sdoc (см. FS §4.3, ADR-0004)."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.document import ListBlock, Paragraph, Section, Table
from core.formula import Formula
from core.xml_parser import XMLParser


def test_parse_minimal(fixtures_dir: Path) -> None:
    doc = XMLParser(str(fixtures_dir / "minimal.sdoc")).parse()
    assert doc.title == "Минимальный документ"
    assert doc.author == "Автор"
    assert doc.language == "ru"


def test_parse_cyrillic(fixtures_dir: Path) -> None:
    doc = XMLParser(str(fixtures_dir / "cyrillic.sdoc")).parse()
    assert doc.title == "Кириллический документ"
    assert len(doc.sections) >= 1
    assert doc.sections[0].heading == "Введение"


def test_parse_formulas(fixtures_dir: Path) -> None:
    doc = XMLParser(str(fixtures_dir / "formulas.sdoc")).parse()
    found: list[Formula] = []
    for block in doc.body:
        found.extend(_collect_formulas(block))
    latexes = {f.latex for f in found}
    assert "E = mc^2" in latexes
    assert any(f.type == "display" for f in found)


def test_parse_table(fixtures_dir: Path) -> None:
    doc = XMLParser(str(fixtures_dir / "table.sdoc")).parse()
    table = doc.body[0]
    assert isinstance(table, Table)
    assert table.cols == 3
    assert len(table.rows_data) == 2


def test_parse_bibliography(fixtures_dir: Path) -> None:
    doc = XMLParser(str(fixtures_dir / "bibliography.sdoc")).parse()
    assert doc.bibliography.style == "GOST"
    assert len(doc.bibliography.entries) == 2
    assert doc.bibliography.entries[0].key == "einstein1905"


def test_invalid_xml_raises(tmp_path: Path) -> None:
    # отсутствует обязательный атрибут version → схема должна отклонить
    bad = tmp_path / "bad.sdoc"
    bad.write_text(
        "<sdoc:sdoc xmlns:sdoc='https://scientificcat.dev/sdoc/1.0'></sdoc:sdoc>",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        XMLParser(str(bad)).parse()


def _collect_formulas(block: object) -> list[Formula]:
    result: list[Formula] = []
    if isinstance(block, Formula):
        result.append(block)
    elif isinstance(block, Paragraph):
        result.extend(block.formulas)
    elif isinstance(block, Section):
        for child in block.children:
            result.extend(_collect_formulas(child))
    elif isinstance(block, ListBlock):
        return result
    return result