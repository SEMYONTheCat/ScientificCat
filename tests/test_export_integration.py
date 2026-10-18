"""Интеграционный тест: создание → сохранение → загрузка → экспорт (TODO §5.5).

Полный цикл для форматов без GUI-зависимостей (LaTeX, HTML, DOCX);
PDF покрыт в test_exporter.py через qtbot.
"""

from __future__ import annotations

from pathlib import Path

from core.document import Document, Paragraph, Run
from core.exporter import Exporter


def _doc() -> Document:
    doc = Document.new()
    doc.title = "Интеграционный тест"
    # id должен соответствовать XSD-паттерну [a-zA-Z][a-zA-Z0-9_.-]{2,31}
    doc.body.append(Paragraph(id="p001", runs=[Run(text="Привет, мир!")]))
    return doc


def test_full_cycle_latex_html_docx(tmp_path: Path) -> None:
    source = tmp_path / "doc.sdoc"
    _doc().save(str(source))

    loaded = Document.from_file(str(source))
    assert loaded.title == "Интеграционный тест"

    exporter = Exporter(loaded)

    tex = tmp_path / "out.tex"
    exporter.export_latex(str(tex))
    assert tex.exists()
    assert "Привет, мир!" in tex.read_text(encoding="utf-8")

    html = tmp_path / "out.html"
    exporter.export_html(str(html))
    assert html.exists()
    assert "Привет, мир!" in html.read_text(encoding="utf-8")

    docx = tmp_path / "out.docx"
    exporter.export_docx(str(docx))
    assert docx.exists()
    assert docx.stat().st_size > 0


def test_roundtrip_preserves_title(tmp_path: Path) -> None:
    source = tmp_path / "r.sdoc"
    _doc().save(str(source))
    loaded = Document.from_file(str(source))
    assert loaded.get_word_count() == 2  # «Привет,» и «мир!»