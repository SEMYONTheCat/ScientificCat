"""Виджет предпросмотра (см. FS §4.10, ADR-0002/0014).

Рендерит Document через IR в HTML и отображает в QWebEngineView,
рендеринг формул — KaTeX из локальных ассетов assets/katex/.
"""

from __future__ import annotations

import html as _html

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView

from core.document import Document
from core.ir import (
    IRFormula,
    IRHeading,
    IRList,
    IRParagraph,
    IRTable,
    IRText,
    document_to_ir,
)
from services.paths import resource_path

KATEX_DIR = resource_path("assets/katex")


class PreviewWidget(QWebEngineView):
    """Предпросмотр HTML-документа с KaTeX-формулами."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.page().settings().setAttribute(
            self.page().settings().WebAttribute.JavascriptEnabled, True
        )

    def render_document(self, document: Document) -> None:
        """Рендеринг всего документа в HTML."""
        html = self._build_html(document)
        self.setHtml(html, QUrl.fromLocalFile(str(KATEX_DIR) + "/"))

    def _build_html(self, document: Document) -> str:
        content = "\n".join(self._render_block(b) for b in document_to_ir(document))
        return _TEMPLATE.format(
            title=_html.escape(document.title or "Scientific Cat"),
            content=content,
        )

    def _render_block(self, block) -> str:
        if isinstance(block, IRHeading):
            return f"<h{block.level}>{_html.escape(block.text)}</h{block.level}>"
        if isinstance(block, IRParagraph):
            items = "".join(self._render_item(i) for i in block.items)
            return f'<p style="text-align:{block.align}">{items}</p>'
        if isinstance(block, IRFormula):
            display = "formula-display" if block.display else ""
            return f'<div class="{display}" data-latex="{_attr(block.latex)}"></div>'
        if isinstance(block, IRList):
            tag = "ol" if block.ordered else "ul"
            items = "".join(f"<li>{_html.escape(i)}</li>" for i in block.items)
            return f"<{tag}>{items}</{tag}>"
        if isinstance(block, IRTable):
            rows = "".join(
                "<tr>"
                + "".join(
                    "<td>"
                    + "".join(self._render_item(item) for item in cell.items)
                    + "</td>"
                    for cell in row
                )
                + "</tr>"
                for row in block.rows
            )
            caption = (
                f"<caption>{_html.escape(block.caption)}</caption>" if block.caption else ""
            )
            return f'<table class="table">{caption}{rows}</table>'
        return ""

    def _render_item(self, item) -> str:
        if isinstance(item, IRText):
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
        if isinstance(item, IRFormula):
            return f'<span data-latex="{_attr(item.latex)}"></span>'
        return ""


def _attr(value: str) -> str:
    return _html.escape(value, quote=True)


_TEMPLATE = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="katex.min.css">
<script src="katex.min.js"></script>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; margin: 30mm 20mm; line-height: 1.5; }}
  .formula-display {{ text-align: center; margin: 1em 0; }}
  table.table {{ border-collapse: collapse; margin: 1em auto; }}
  .table td {{ border: 1px solid #ccc; padding: 6px 10px; }}
  h1, h2, h3 {{ margin: 0.8em 0 0.3em; }}
</style>
</head><body>
{content}
<script>
  document.querySelectorAll('[data-latex]').forEach(function(el) {{
    try {{
      katex.render(el.getAttribute('data-latex'), el, {{
        throwOnError: false,
        displayMode: el.classList.contains('formula-display')
      }});
    }} catch(e) {{ el.textContent = el.getAttribute('data-latex'); }}
  }});
</script>
</body></html>"""