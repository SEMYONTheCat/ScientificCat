"""Тесты модели Document (см. FS §4.1, ADR-0005)."""

from __future__ import annotations

from core.document import Document, Paragraph, Run, Section
from core.formula import Formula


class TestDocument:
    def test_create_new_document(self) -> None:
        doc = Document.new()
        assert doc.title == ""
        assert doc.author == ""
        assert doc.body == []
        assert doc.styles.language == "ru"

    def test_default_styles_present(self) -> None:
        doc = Document.new()
        assert "Main" in doc.styles.fonts
        assert "Body" in doc.styles.styles

    def test_word_count(self) -> None:
        doc = Document.new()
        section = Section(id="sec01", heading="Введение")
        p = Paragraph(id="p01")
        p.runs.append(Run(text="Три слова здесь"))
        section.children.append(p)
        doc.body.append(section)
        assert doc.get_word_count() == 4  # "Введение" + 3 слова

    def test_no_get_page_count_in_core(self) -> None:
        # Пагинация вынесена из ядра (ADR-0005)
        assert not hasattr(Document, "get_page_count")

    def test_insert_formula_object(self) -> None:
        # Модель не мутируется напрямую (Command-паттерн в ADR-0013),
        # но Formula можно хранить в Paragraph.
        p = Paragraph(id="p01")
        p.formulas.append(Formula(latex="E = mc^2"))
        assert len(p.formulas) == 1