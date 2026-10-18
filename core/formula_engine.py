"""Движок формул (см. FS §4.4, ADR-0002/0003).

Валидация и базовые преобразования выполняются в ядре без Qt/WebEngine.
Экранный рендер KaTeX выполняется в UI (QWebEngineView); здесь — обёртки
и опциональный matplotlib-бэкенд для PNG (экспорт DOCX, ADR-0006).
"""

from __future__ import annotations

import html as _html

from pylatexenc.latex2text import LatexNodes2Text


class FormulaEngine:
    """Конвейер формул: валидация, HTML-обёртка, PNG-рендер."""

    def validate_latex(self, latex: str) -> tuple[bool, str]:
        """Быстрая структурная проверка через pylatexenc.

        Авторитетная проверка полноты — KaTeX (ADR-0003), вызывается
        из UI, где доступен рендер.
        """
        try:
            LatexNodes2Text().latex_to_text(latex)
            return True, ""
        except Exception as exc:  # noqa: BLE001 - валидация принимает любые ошибки
            return False, str(exc)

    def latex_to_html(self, latex: str, display: bool = False) -> str:
        """LaTeX → HTML-обёртка (KaTeX-спан).

        Фактический рендер в браузере выполняет KaTeX; здесь формула
        помещается в контейнер с классом katex.
        """
        css = "katex katex-display" if display else "katex"
        return f'<span class="{css}">{_html.escape(latex)}</span>'

    def latex_to_png(self, latex: str, dpi: int = 300) -> bytes:
        """LaTeX → PNG через matplotlib (опциональный бэкенд, ADR-0002)."""
        try:
            import io  # noqa: PLC0415 - ленивый опциональный импорт

            import matplotlib.pyplot as plt  # noqa: PLC0415 - ленивый опциональный импорт
        except ImportError as exc:
            raise RuntimeError(
                "matplotlib не установлен (опциональная зависимость для PNG-экспорта)"
            ) from exc

        fig = plt.figure(figsize=(0.01, 0.01), dpi=dpi)
        fig.patch.set_alpha(0)
        fig.text(0, 0, f"${latex}$", ha="left", va="bottom", fontsize=14)
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=dpi,
            bbox_inches="tight",
            transparent=True,
            pad_inches=0.01,
        )
        plt.close(fig)
        return buf.getvalue()