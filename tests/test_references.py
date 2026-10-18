"""Тесты перекрёстных ссылок и авто-нумерации (см. ADR-0011)."""

from __future__ import annotations

from core.document import Document, Formula, Paragraph, Section
from core.references import ReferenceResolver


def _doc() -> Document:
    doc = Document.new()
    doc.body.append(Section(id="s1", level=1, heading="Введение"))
    s2 = Section(id="s2", level=1, heading="Методы")
    s2.children.append(Section(id="s2a", level=2, heading="Подход"))
    doc.body.append(s2)
    doc.body.append(Paragraph(id="p1", formulas=[Formula("x^2", "display", number=0)]))
    return doc


class TestNumberSections:
    def test_numbering(self) -> None:
        doc = _doc()
        ReferenceResolver(doc).number_sections()
        assert doc.body[0].number == "1"
        assert doc.body[1].number == "2"
        sub = doc.body[1].children[0]
        assert isinstance(sub, Section) and sub.number == "2.1"


class TestNumberFormulas:
    def test_formula_numbering(self) -> None:
        doc = _doc()
        ReferenceResolver(doc).number_formulas()
        para = doc.body[2]
        assert isinstance(para, Paragraph)
        assert para.formulas[0].number == 1
        named = doc.named_objects[para.formulas[0].id]
        assert named.obj_type == "equation"
        assert named.label == "1"


class TestResolve:
    def test_register_and_resolve(self) -> None:
        doc = Document.new()
        resolver = ReferenceResolver(doc)
        ref_id = resolver.register("formula", label="2")
        assert resolver.resolve(ref_id) == "уравнение (2)"

    def test_resolve_unknown(self) -> None:
        resolver = ReferenceResolver(Document.new())
        assert resolver.resolve("nope") == "???"

    def test_resolve_without_label(self) -> None:
        doc = Document.new()
        resolver = ReferenceResolver(doc)
        ref_id = resolver.register("table")
        assert resolver.resolve(ref_id) == "таблица"