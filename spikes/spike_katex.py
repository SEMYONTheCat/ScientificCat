"""Spike B (ADR-0002/0003): KaTeX в QWebEngineView + валидация LaTeX.

Проверяет:
  1) pylatexenc — быстрая синтаксическая проверка (без ложных ошибок
     на матрицах/окружениях, в отличие от sympy);
  2) KaTeX c throwOnError — авторитетная проверка полноты формулы
     (ловит обрывы вроде `\\frac{`), работает через QWebEngineView
     с локальными ассетами assets/katex/.

Запуск headless:
    set QT_QPA_PLATFORM=offscreen & .venv\\Scripts\\python.exe spikes\\spike_katex.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pylatexenc.latexwalker import LatexWalker, LatexWalkerError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KATEX_DIR = PROJECT_ROOT / "assets" / "katex"

# Формулы: (имя, latex, ожидаемая валидность, display-режим)
FORMULAS: list[tuple[str, str, bool, bool]] = [
    ("simple", r"E = mc^2", True, False),
    ("fraction", r"\frac{a+b}{c-d}", True, False),
    ("integral", r"\int_0^\infty e^{-x} dx = 1", True, False),
    ("matrix", r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}", True, False),
    ("align", r"\begin{align} a &= b \\ c &= d \end{align}", True, True),
    ("broken", r"x^ + \frac{", False, False),
]


def validate_pylatexenc(latex: str) -> tuple[bool, str]:
    """Быстрая проверка структуры через pylatexenc (лояльная)."""
    try:
        LatexWalker(latex).get_latex_nodes()
        return True, ""
    except LatexWalkerError as e:
        return False, str(e)


HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="katex.min.css">
<script src="katex.min.js"></script>
</head><body>
<div id="target"></div>
<script>
  window.renderFormula = function(latex, display) {
    try {
      var el = document.getElementById('target');
      katex.render(latex, el, {throwOnError: false, displayMode: !!display});
      return JSON.stringify({ok: true, error: '', html: el.innerHTML});
    } catch (e) { return JSON.stringify({ok: false, error: e.message, html: ''}); }
  };
  window.checkFormula = function(latex, display) {
    try {
      katex.render(latex, document.createElement('div'),
                   {throwOnError: true, displayMode: !!display});
      return JSON.stringify({ok: true, error: ''});
    } catch (e) { return JSON.stringify({ok: false, error: e.message}); }
  };
</script>
</body></html>"""


def run_validation() -> None:
    print("== pylatexenc: быстрая структурная проверка ==")
    for name, latex, _expected, _disp in FORMULAS:
        ok, detail = validate_pylatexenc(latex)
        print(f"  {name:10s} -> {'OK' if ok else 'FAIL (' + detail + ')'}")


def run_katex_checks() -> bool:
    from PySide6.QtCore import QEventLoop, QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    print("\n== KaTeX (QWebEngineView): авторитетная проверка + рендер ==")
    app = QApplication.instance() or QApplication(sys.argv)
    view = QWebEngineView()

    loop = QEventLoop()
    view.loadFinished.connect(lambda ok: loop.quit())
    view.setHtml(HTML, QUrl.fromLocalFile(str(KATEX_DIR) + "/"))
    loop.exec()

    def _run_js(script: str) -> str:
        inner = QEventLoop()
        result: list[str] = []
        view.page().runJavaScript(script, lambda res: (result.append(str(res)), inner.quit()))
        inner.exec()
        return result[0] if result else "{}"

    all_ok = True
    for name, latex, expected, display in FORMULAS:
        raw = _run_js(f"checkFormula({latex!r}, {str(display).lower()})")
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"ok": False, "error": f"bad js response: {raw[:40]}"}
        ok = bool(res.get("ok"))
        matched = ok == expected
        all_ok = all_ok and matched
        status = "OK" if ok else f"REJECTED ({res.get('error', '')[:60]})"
        print(f"  {name:10s} expect={str(expected):5s} got={status:12s} [{('PASS' if matched else 'MISMATCH')}]")

    # Рендер одной валидной формулы (демонстрация JS-bridge)
    rendered_raw = _run_js("renderFormula('E = mc^2', false)")
    try:
        rendered = json.loads(rendered_raw)
    except json.JSONDecodeError:
        rendered = {}
    has_katex = "katex" in str(rendered.get("html", ""))
    print(f"\n  Rendered HTML contains 'katex': {has_katex}")

    view.deleteLater()
    return all_ok and has_katex


def main() -> int:
    run_validation()
    ok = run_katex_checks()
    print("\nSpike B:", "PASS" if ok else "FAIL")
    sys.stdout.flush()
    sys.stderr.flush()
    # os._exit обходит краш QtWebEngine при выходе в offscreen-режиме
    os._exit(0 if ok else 1)  # noqa: PLR1722


if __name__ == "__main__":
    main()