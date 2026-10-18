# ADR-0002: Конвейер рендеринга формул

- **Статус:** Accepted
- **Дата:** 2026-08-18
- **Связанные документы:** [`FS.md`](../../FS.md) §4.4; [`TZ.md`](../../TZ.md) §2.4

## Контекст

Спецификация объявляет `FormulaEngine.latex_to_svg()` как «вызов KaTeX через
Qt WebEngine JS bridge». Но **KaTeX рендерит формулы в HTML+CSS**, а не в SVG.
Нативная выдача KaTeX — `<span class="katex">...` с inline-стилями.
Требования по экспорту (ТЗ Р-02 — PDF через SVG, Р-03 — DOCX через PNG)
нуждаются в SVG и PNG бэкендах, которых у KaTeX нет.

## Решение

Зафиксировать **единый конвейер рендеринга** с разделением бэкендов по целям:

| Цель                     | Бэкенд                     | Формат вывода |
|--------------------------|----------------------------|---------------|
| Экран / Live preview     | KaTeX (QWebEngineView)     | HTML + CSS    |
| Экспорт PDF              | MathJax-SVG либо matplotlib | SVG           |
| Экспорт DOCX             | matplotlib                 | PNG           |
| Валидация LaTeX          | pylatexenc + KaTeX throwOnError | —            |

Структура `FormulaEngine`:

```python
class FormulaEngine:
    def latex_to_html(self, latex: str) -> str:   # KaTeX (экран)
    def latex_to_svg(self, latex: str) -> str:    # MathJax-svg / matplotlib (PDF)
    def latex_to_png(self, latex: str, dpi: int) -> bytes:  # matplotlib (DOCX)
    def validate_latex(self, latex: str) -> tuple[bool, str]:  # pylatexenc + KaTeX
```

В методе `latex_to_svg()` **исключается** вызов KaTeX через JS bridge;
SVG генерируется бэкендом, поддерживающим SVG напрямую.

## Последствия

- Убирается ошибочная связка «KaTeX → SVG».
- PDF и DOCX получают стабильные бэкенды (SVG/PNG).
- Требуется опциональная зависимость matplotlib и/или MathJax-SVG
  (см. ADR-0003 про валидацию и окружение).
- HTML-экспорт (Р-04) продолжает использовать KaTeX CDN.

## Результат спайка (2026-08-18)

**Подтверждено** на `spikes/spike_katex.py`:
- KaTeX рендерит формулу в `QWebEngineView` через **локальные ассеты**
  `assets/katex/` (katex.min.js/css), результат возвращается по JS-bridge
  (JSON-строкой). Решение жизнеспособно.
- Замечание: для полного офлайна требуется бандлизация **шрифтов KaTeX**
  (fonts/*.woff2), т.к. локальные CSS ссылаются на `fonts/…`.
  На этапе спайка рендер работает с fallback-шрифтами.
- Спайк запускается с `QT_QPA_PLATFORM=offscreen`; при завершении процесса
  QtWebEngine может падать с access violation — обходится `os._exit` в
  headless-сценарии (артефакт offscreen, на реальном дисплее не проявляется).