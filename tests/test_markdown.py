"""Тесты Markdown импорта/экспорта (см. TZ Т-07)."""

from __future__ import annotations

from core.document import ListBlock, Paragraph, Section
from core.markdown import document_to_md, md_to_document


def test_md_to_document_heading() -> None:
    doc = md_to_document("# Заголовок\n\nТекст абзаца.\n")
    sections = [b for b in doc.body if isinstance(b, Section)]
    assert sections and sections[0].heading == "Заголовок"
    assert sections[0].level == 1


def test_md_to_document_subheading_level() -> None:
    doc = md_to_document("## Подраздел")
    sec = [b for b in doc.body if isinstance(b, Section)][0]
    assert sec.level == 2


def test_md_to_document_paragraph() -> None:
    doc = md_to_document("Обычный абзац текста.\n")
    paras = [b for b in doc.body if isinstance(b, Paragraph)]
    assert paras and "Обычный абзац" in paras[0].runs[0].text


def test_md_to_document_list() -> None:
    doc = md_to_document("- пункт 1\n- пункт 2\n")
    lists = [b for b in doc.body if isinstance(b, ListBlock)]
    assert lists and len(lists[0].items) == 2


def test_md_to_document_bold_emphasis() -> None:
    doc = md_to_document("Текст **жирный** и *курсив*.\n")
    paras = [b for b in doc.body if isinstance(b, Paragraph)]
    assert "**жирный**" in paras[0].runs[0].text


def test_document_to_md_contains_heading() -> None:
    doc = md_to_document("# Заголовок\n\nабзац\n")
    out = document_to_md(doc)
    assert "# Заголовок" in out