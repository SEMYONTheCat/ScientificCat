"""Система экспорта (см. FS §4.5, ADR-0006).

Единый конвейер: Document → IR → формат.
Формулы в IR хранятся как LaTeX; в DOCX рендерятся в PNG (matplotlib),
в PDF встраиваются как текст/место.
"""

from __future__ import annotations

import base64
import html as _html
import io
from pathlib import Path
from typing import Any

from core.document import Document
from core.formula_engine import FormulaEngine
from core.ir import (
    IRBlock,
    IRFormula,
    IRHeading,
    IRList,
    IRParagraph,
    IRTable,
    IRText,
    document_to_ir,
)


class Exporter:
    """Экспорт Document в PDF/DOCX/HTML/LaTeX."""

    def __init__(self, document: Document) -> None:
        self.document = document
        self.engine = FormulaEngine()

    # ---------- LaTeX ----------

    def export_latex(self, output_path: str) -> None:
        body = "\n".join(self._latex_block(b) for b in document_to_ir(self.document))
        tex = (
            "\\documentclass[12pt]{article}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage[english,russian]{babel}\n"
            "\\usepackage{amsmath, amsfonts}\n"
            f"\\title{{{_tex_escape(self.document.title)}}}\n"
            "\\begin{document}\n"
            f"{body}\n"
            "\\end{document}\n"
        )
        Path(output_path).write_text(tex, encoding="utf-8")

    def _latex_block(self, block: IRBlock) -> str:
        if isinstance(block, IRHeading):
            cmd = "section" if block.level == 1 else "subsection"
            return f"\\{cmd}{{{_tex_escape(block.text)}}}"
        if isinstance(block, IRParagraph):
            items = "".join(
                f"${item.latex}$" if isinstance(item, IRFormula) else self._latex_text(item)
                for item in block.items
            )
            return items + "\\\\"
        if isinstance(block, IRFormula):
            open_delim = "\\[" if block.display else "$"
            close_delim = "\\]" if block.display else "$"
            return f"{open_delim}{block.latex}{close_delim}"
        if isinstance(block, IRList):
            env = "enumerate" if block.ordered else "itemize"
            items = "\n".join(f"\\item {_tex_escape(i)}" for i in block.items)
            return f"\\begin{{{env}}}\n{items}\n\\end{{{env}}}"
        if isinstance(block, IRTable):
            return self._latex_table(block)
        return ""

    def _latex_text(self, item: IRText) -> str:
        text = _tex_escape(item.text)
        if item.subscript:
            text = f"\\textsubscript{{{text}}}"
        elif item.superscript:
            text = f"\\textsuperscript{{{text}}}"
        if item.underline:
            text = f"\\underline{{{text}}}"
        if item.italic:
            text = f"\\textit{{{text}}}"
        if item.bold:
            text = f"\\textbf{{{text}}}"
        return text

    def _latex_table(self, table: IRTable) -> str:
        if not table.rows:
            return ""
        cols = "c" * len(table.rows[0])
        lines = ["\\begin{table}", f"\\begin{{tabular}}{{{cols}}}"]
        for row in table.rows:
            lines.append(
                " & ".join(
                    "".join(
                        f"${item.latex}$"
                        if isinstance(item, IRFormula)
                        else self._latex_text(item)
                        for item in cell.items
                    )
                    for cell in row
                )
                + " \\\\"
            )
        lines.append("\\end{tabular}")
        if table.caption:
            lines.append(f"\\caption{{{_tex_escape(table.caption)}}}")
        lines.append("\\end{table}")
        return "\n".join(lines)

    # ---------- HTML ----------

    def export_html(self, output_path: str) -> None:
        content = "\n".join(self._html_block(b) for b in document_to_ir(self.document))
        html = _HTML_TEMPLATE.format(title=_html.escape(self.document.title), content=content)
        Path(output_path).write_text(html, encoding="utf-8")

    def _html_block(self, block: IRBlock) -> str:
        if isinstance(block, IRHeading):
            return f"<h{block.level}>{_html.escape(block.text)}</h{block.level}>"
        if isinstance(block, IRParagraph):
            items = "".join(
                f'<span class="katex">{_html.escape(item.latex)}</span>'
                if isinstance(item, IRFormula)
                else self._html_text(item)
                for item in block.items
            )
            return f"<p>{items}</p>"
        if isinstance(block, IRFormula):
            cls = "katex-display" if block.display else "katex"
            return f'<div class="{cls}">{_html.escape(block.latex)}</div>'
        if isinstance(block, IRList):
            tag = "ol" if block.ordered else "ul"
            items = "".join(f"<li>{_html.escape(i)}</li>" for i in block.items)
            return f"<{tag}>{items}</{tag}>"
        if isinstance(block, IRTable):
            rows = "".join(
                "<tr>"
                + "".join(
                    "<td>"
                    + "".join(
                        f'<span class="katex">{_html.escape(item.latex)}</span>'
                        if isinstance(item, IRFormula)
                        else self._html_text(item)
                        for item in cell.items
                    )
                    + "</td>"
                    for cell in row
                )
                + "</tr>"
                for row in block.rows
            )
            caption = (
                f"<caption>{_html.escape(block.caption)}</caption>"
                if block.caption
                else ""
            )
            return f"<table>{caption}<tbody>{rows}</tbody></table>"
        return ""

    @staticmethod
    def _html_text(item: IRText) -> str:
        text = _html.escape(item.text)
        if item.subscript:
            text = f"<sub>{text}</sub>"
        elif item.superscript:
            text = f"<sup>{text}</sup>"
        if item.underline:
            text = f"<u>{text}</u>"
        if item.italic:
            text = f"<em>{text}</em>"
        if item.bold:
            text = f"<strong>{text}</strong>"
        return text

    # ---------- DOCX ----------

    def export_docx(self, output_path: str, dpi: int = 300) -> None:
        from docx import Document as DocxDocument  # noqa: PLC0415

        doc = DocxDocument()
        doc.add_heading(self.document.title or "Document", level=0)
        for block in document_to_ir(self.document):
            self._docx_block(doc, block, dpi)
        doc.save(output_path)

    def _docx_block(  # noqa: PLR0912
        self, doc: Any, block: IRBlock, dpi: int
    ) -> None:
        if isinstance(block, IRHeading):
            doc.add_heading(block.text, level=min(block.level, 4))
        elif isinstance(block, IRParagraph):
            p = doc.add_paragraph()
            for item in block.items:
                if isinstance(item, IRFormula):
                    self._add_formula_image(p, item, dpi)
                elif item.text:
                    run = p.add_run(item.text)
                    run.bold = item.bold
                    run.italic = item.italic
                    run.underline = item.underline
                    run.font.subscript = item.subscript
                    run.font.superscript = item.superscript
        elif isinstance(block, IRFormula):
            self._add_formula_image(doc.add_paragraph(), block, dpi)
        elif isinstance(block, IRList):
            for i in block.items:
                style = "List Number" if block.ordered else "List Bullet"
                doc.add_paragraph(i, style=style)
        elif isinstance(block, IRTable):
            ncols = len(block.rows[0]) if block.rows else 1
            if block.caption:
                doc.add_paragraph(block.caption, style="Caption")
            table = doc.add_table(rows=len(block.rows), cols=ncols)
            for r, row in enumerate(block.rows):
                for c, cell in enumerate(row):
                    paragraph = table.cell(r, c).paragraphs[0]
                    for item in cell.items:
                        if isinstance(item, IRFormula):
                            self._add_formula_image(paragraph, item, dpi)
                        elif item.text:
                            run = paragraph.add_run(item.text)
                            run.bold = item.bold
                            run.italic = item.italic
                            run.underline = item.underline
                            run.font.subscript = item.subscript
                            run.font.superscript = item.superscript

    def _add_formula_image(self, paragraph: Any, formula: IRFormula, dpi: int) -> None:
        try:
            png = self.engine.latex_to_png(formula.latex, dpi=dpi)
            run = paragraph.add_run()
            run.add_picture(io.BytesIO(png))
        except RuntimeError:
            paragraph.add_run(f"[{formula.latex}]")

    # ---------- PDF ----------

    def export_pdf(self, output_path: str, dpi: int = 300) -> None:
        from PySide6.QtGui import QPdfWriter, QTextDocument  # noqa: PLC0415

        writer = QPdfWriter(output_path)
        writer.setResolution(dpi)
        doc = QTextDocument()
        doc.setHtml(self._pdf_html(dpi))
        doc.print_(writer)

    def _pdf_html(self, dpi: int) -> str:
        body = "\n".join(self._pdf_block(block, dpi) for block in document_to_ir(self.document))
        return (
            "<html><head><meta charset=\"utf-8\"><style>"
            "body{font-family:Georgia,'Times New Roman',serif;font-size:12pt;}"
            "h1,h2,h3,h4,h5,h6{margin-top:18px;margin-bottom:8px;}"
            "p{margin:6px 0;} .formula{text-align:center;margin:10px 0;}"
            "table{border-collapse:collapse;margin:8px auto;}"
            "td{border:1px solid #777;padding:4px 8px;}"
            "</style></head><body>"
            f"<h1>{_html.escape(self.document.title)}</h1>{body}</body></html>"
        )

    def _pdf_block(self, block: IRBlock, dpi: int) -> str:
        if isinstance(block, IRHeading):
            return f"<h{block.level}>{_html.escape(block.text)}</h{block.level}>"
        if isinstance(block, IRParagraph):
            items = "".join(
                self._formula_image_html(item, dpi)
                if isinstance(item, IRFormula)
                else self._html_text(item)
                for item in block.items
            )
            return f'<p style="text-align:{block.align}">{items}</p>'
        if isinstance(block, IRFormula):
            return f'<div class="formula">{self._formula_image_html(block, dpi)}</div>'
        if isinstance(block, IRList):
            tag = "ol" if block.ordered else "ul"
            items = "".join(f"<li>{_html.escape(item)}</li>" for item in block.items)
            return f"<{tag}>{items}</{tag}>"
        if isinstance(block, IRTable):
            rows = "".join(
                "<tr>"
                + "".join(
                    "<td>"
                    + "".join(
                        self._formula_image_html(item, dpi)
                        if isinstance(item, IRFormula)
                        else self._html_text(item)
                        for item in cell.items
                    )
                    + "</td>"
                    for cell in row
                )
                + "</tr>"
                for row in block.rows
            )
            caption = (
                f"<caption>{_html.escape(block.caption)}</caption>"
                if block.caption
                else ""
            )
            return f"<table>{caption}{rows}</table>"
        return ""

    def _formula_image_html(self, formula: IRFormula, dpi: int) -> str:
        try:
            png = self.engine.latex_to_png(formula.latex, dpi=dpi)
        except RuntimeError:
            return f"<code>{_html.escape(formula.latex)}</code>"
        encoded = base64.b64encode(png).decode("ascii")
        alt = _html.escape(formula.latex, quote=True)
        return f'<img src="data:image/png;base64,{encoded}" alt="{alt}">'


def _tex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "#": r"\#",
        "$": r"\$",
        "%": r"\%",
        "&": r"\&",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(char, char) for char in text)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>body {{ font-family: Georgia, serif; margin: 40px; }} table {{ border-collapse: collapse; }}
td {{ border: 1px solid #999; padding: 4px 8px; }}</style>
</head><body>
{content}
<script>
document.addEventListener("DOMContentLoaded", function() {{
  document.querySelectorAll('.katex').forEach(function(el){{
    var opts = {{throwOnError:false, displayMode: el.classList.contains('katex-display')}};
    try {{ katex.render(el.textContent, el, opts); }}
    catch(e) {{ }}
  }});
}});
</script>
</body></html>"""