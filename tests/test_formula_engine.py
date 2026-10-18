"""Тесты движка формул и IR (см. ADR-0002/0003/0006)."""

from __future__ import annotations

from core.formula_engine import FormulaEngine
from core.ir import IRFormula, IRHeading, IRParagraph, IRText, document_to_ir
from core.xml_parser import XMLParser


class TestFormulaEngine:
    def setup_method(self) -> None:
        self.engine = FormulaEngine()

    def test_validate_valid(self) -> None:
        ok, msg = self.engine.validate_latex(r"\int_0^\infty e^{-x} dx")
        assert ok is True
        assert msg == ""

    def test_validate_matrix_no_false_error(self) -> None:
        ok, _ = self.engine.validate_latex(r"\begin{pmatrix}1&2\\3&4\end{pmatrix}")
        assert ok is True

    def test_latex_to_html_inline(self) -> None:
        html = self.engine.latex_to_html("E = mc^2")
        assert 'class="katex"' in html
        assert "mc" in html

    def test_latex_to_html_display(self) -> None:
        html = self.engine.latex_to_html("E = mc^2", display=True)
        assert "katex-display" in html


class TestIR:
    def test_document_to_ir_structure(self, fixtures_dir) -> None:
        doc = XMLParser(str(fixtures_dir / "formulas.sdoc")).parse()
        blocks = document_to_ir(doc)
        assert any(isinstance(b, IRParagraph) for b in blocks)
        # IRFormula встречается и как элемент параграфа, и как блок верхнего уровня
        formulas: list[IRFormula] = []
        for block in blocks:
            if isinstance(block, IRFormula):
                formulas.append(block)
            elif isinstance(block, IRParagraph):
                formulas.extend(i for i in block.items if isinstance(i, IRFormula))
        assert any(f.latex == "E = mc^2" for f in formulas)
        assert any(f.display for f in formulas)

    def test_heading_in_ir(self, fixtures_dir) -> None:
        doc = XMLParser(str(fixtures_dir / "cyrillic.sdoc")).parse()
        blocks = document_to_ir(doc)
        headings = [b for b in blocks if isinstance(b, IRHeading)]
        assert any(h.text == "Введение" for h in headings)

    def test_text_style_preserved(self, fixtures_dir) -> None:
        doc = XMLParser(str(fixtures_dir / "minimal.sdoc")).parse()
        blocks = document_to_ir(doc)
        texts = [
            t
            for block in blocks
            if isinstance(block, IRParagraph)
            for t in block.items
            if isinstance(t, IRText)
        ]
        assert texts and texts[0].text  # непустой текст присутствует