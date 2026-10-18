"""Тесты системы экспорта (см. FS §4.5, ADR-0006)."""

from __future__ import annotations

from core.document import BibEntry, Cell, Document, Paragraph, Row, Run, Table
from core.exporter import Exporter
from core.formula import Formula
from core.ir import IRTable, document_to_ir
from core.xml_parser import XMLParser


def _make_document(fixtures_dir) -> object:
    return XMLParser(str(fixtures_dir / "formulas.sdoc")).parse()


class TestExporter:
    def test_export_latex(self, tmp_path, fixtures_dir) -> None:
        out = tmp_path / "doc.tex"
        Exporter(_make_document(fixtures_dir)).export_latex(str(out))
        content = out.read_text(encoding="utf-8")
        assert "\\begin{document}" in content
        assert "E = mc^2" in content

    def test_export_html(self, tmp_path, fixtures_dir) -> None:
        out = tmp_path / "doc.html"
        Exporter(_make_document(fixtures_dir)).export_html(str(out))
        content = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "katex" in content

    def test_export_docx(self, tmp_path, fixtures_dir) -> None:
        out = tmp_path / "doc.docx"
        Exporter(_make_document(fixtures_dir)).export_docx(str(out))
        assert out.is_file()
        assert out.stat().st_size > 0

    def test_export_pdf(self, qtbot, tmp_path, fixtures_dir) -> None:
        out = tmp_path / "doc.pdf"
        Exporter(_make_document(fixtures_dir)).export_pdf(str(out))
        assert out.is_file()
        assert out.stat().st_size > 0
        assert b"/Subtype /Image" in out.read_bytes()

    def test_pdf_html_contains_formatting_and_rendered_formula(self, monkeypatch) -> None:
        doc = Document.new()
        doc.title = "Форматированный документ"
        paragraph = Paragraph(id="p001")
        text = Run("Важно", bold=True, superscript=True)
        formula = Formula("x^2", formula_id="eq000001")
        paragraph.runs.append(text)
        paragraph.formulas.append(formula)
        paragraph.content.extend([text, formula])
        doc.body.append(paragraph)
        exporter = Exporter(doc)
        monkeypatch.setattr(
            exporter.engine,
            "latex_to_png",
            lambda latex, dpi: b"rendered-png",
        )

        html = exporter._pdf_html(240)

        assert "<strong>" in html
        assert "<sup>" in html
        assert "data:image/png;base64," in html
        assert "cmVuZGVyZWQtcG5n" in html

    def test_export_includes_generated_bibliography(self, tmp_path) -> None:
        doc = Document.new()
        doc.bibliography.entries.append(
            BibEntry(
                key="einstein1905",
                author="Эйнштейн, А.",
                title="Об электродинамике",
                year="1905",
            )
        )
        output = tmp_path / "bibliography.html"

        Exporter(doc).export_html(str(output))
        html = output.read_text(encoding="utf-8")

        assert "Список литературы" in html
        assert "Эйнштейн" in html

    def test_table_formula_and_caption_reach_all_exporters(self, monkeypatch) -> None:
        doc = Document.new()
        formula = Formula("x^2", formula_id="eq-table")
        text = Run("Значение: ", bold=True)
        cell = Cell(
            runs=[text],
            formulas=[formula],
            content=[text, formula],
        )
        doc.body.append(
            Table(
                id="table-1",
                cols=1,
                rows=1,
                caption="Результаты & расчёты",
                rows_data=[Row(cells=[cell])],
            )
        )
        exporter = Exporter(doc)
        monkeypatch.setattr(
            exporter.engine,
            "latex_to_png",
            lambda latex, dpi: b"rendered-png",
        )
        table = document_to_ir(doc)[0]
        assert isinstance(table, IRTable)

        latex = exporter._latex_block(table)
        html = exporter._html_block(table)
        pdf_html = exporter._pdf_block(table, 240)

        assert r"\caption{Результаты \& расчёты}" in latex
        assert "$x^2$" in latex
        assert "<strong>Значение: </strong>" in html
        assert '<span class="katex">x^2</span>' in html
        assert "Результаты &amp; расчёты" in html
        assert "data:image/png;base64," in pdf_html

    def test_latex_export_escapes_all_reserved_text_characters(self, tmp_path) -> None:
        doc = Document.new()
        doc.title = r"A_B & 50% #1 {draft} $5 ^ ~ \ path"
        doc.body.append(
            Paragraph(
                id="p1",
                runs=[Run(r"A_B & 50% #1 {draft} $5 ^ ~ \ path")],
            )
        )
        output = tmp_path / "escaped.tex"

        Exporter(doc).export_latex(str(output))
        latex = output.read_text(encoding="utf-8")

        for escaped in (
            r"\_",
            r"\&",
            r"\%",
            r"\#",
            r"\{",
            r"\}",
            r"\$",
            r"\textasciicircum{}",
            r"\textasciitilde{}",
            r"\textbackslash{}",
        ):
            assert escaped in latex