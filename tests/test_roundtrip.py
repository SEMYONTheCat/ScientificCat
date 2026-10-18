"""Gold-тесты round-trip .sdoc (см. ADR-0007, критерий приёмки №1)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import lxml.etree as ET

from core.document import Document, Paragraph, ParagraphStyle, Run, Section
from core.formula import Formula
from core.ir import IRParagraph, IRText, document_to_ir
from core.xml_serializer import XMLSerializer


def test_roundtrip_all_fixtures(fixtures_dir: Path) -> None:
    """parse → serialize → parse: метаданные и заголовки сохраняются."""
    for fixture in sorted(fixtures_dir.glob("*.sdoc")):
        doc = Document.from_file(fixture)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / fixture.name
            XMLSerializer(doc, str(out)).serialize()
            doc2 = Document.from_file(out)
            assert doc2.title == doc.title
            assert doc2.language == doc.language


def test_roundtrip_formula_latex_preserved(fixtures_dir: Path) -> None:
    """LaTeX-исходники формул не теряются при round-trip."""
    fixture = fixtures_dir / "formulas.sdoc"
    doc = Document.from_file(fixture)
    latexes_before = _collect_latexes(doc)
    assert latexes_before, "фикстура formulas должна содержать формулы"

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "formulas.sdoc"
        XMLSerializer(doc, str(out)).serialize()
        doc2 = Document.from_file(out)
        latexes_after = _collect_latexes(doc2)

    assert latexes_before == latexes_after


def test_serialized_xml_valid_against_schema(fixtures_dir: Path) -> None:
    """Сериализованный XML валиден по XSD."""
    from core.xml_parser import SCHEMA_PATH  # noqa: PLC0415 - локальный импорт константы

    schema = ET.XMLSchema(ET.parse(str(SCHEMA_PATH)))
    fixture = fixtures_dir / "minimal.sdoc"
    doc = Document.from_file(fixture)
    xml_str = XMLSerializer(doc, "").to_string()
    parsed = ET.fromstring(xml_str.encode("utf-8"))
    assert schema.validate(parsed), schema.error_log.last_error.message


def test_roundtrip_preserves_inline_order_and_formatting(tmp_path: Path) -> None:
    doc = Document.new()
    paragraph = Paragraph(id="p001")
    before = Run("до ", bold=True, reference_target="eq000001")
    formula = Formula("x^2", formula_id="eq000001")
    after = Run(" после", italic=True, superscript=True, citation_key="source1")
    paragraph.runs.extend([before, after])
    paragraph.formulas.append(formula)
    paragraph.content.extend([before, formula, after])
    doc.body.append(paragraph)

    path = tmp_path / "ordered.sdoc"
    doc.save(path)
    restored = Document.from_file(path)
    restored_paragraph = restored.body[0]

    assert isinstance(restored_paragraph, Paragraph)
    assert [
        item.latex if isinstance(item, Formula) else item.text
        for item in restored_paragraph.inline_content()
    ] == ["до ", "x^2", " после"]
    assert restored_paragraph.runs[0].bold is True
    assert restored_paragraph.runs[0].reference_target == "eq000001"
    assert restored_paragraph.runs[1].italic is True
    assert restored_paragraph.runs[1].superscript is True
    assert restored_paragraph.runs[1].citation_key == "source1"


def test_named_style_roundtrip_and_ir_inheritance(tmp_path: Path) -> None:
    doc = Document.new()
    doc.styles.styles["Emphasis"] = ParagraphStyle(
        name="Emphasis",
        font="Main",
        size=12,
        italic=True,
        underline=True,
        align="left",
    )
    doc.body.append(
        Paragraph(
            id="p-style",
            runs=[Run("Стиль", style="Emphasis")],
        )
    )
    path = tmp_path / "styles.sdoc"

    doc.save(path)
    restored = Document.from_file(path)
    style = restored.styles.styles["Emphasis"]
    paragraph = document_to_ir(restored)[0]

    assert style.italic is True
    assert style.underline is True
    assert isinstance(paragraph, IRParagraph)
    text = paragraph.items[0]
    assert isinstance(text, IRText)
    assert text.italic is True
    assert text.underline is True


def _collect_latexes(doc: Document) -> list[str]:
    latexes: list[str] = []
    for block in doc.body:
        _collect_block(block, latexes)
    return latexes


def _collect_block(block, out: list[str]) -> None:
    if isinstance(block, Formula):
        out.append(block.latex)
    elif isinstance(block, Paragraph):
        out.extend(f.latex for f in block.formulas)
    elif isinstance(block, Section):
        for child in block.children:
            _collect_block(child, out)