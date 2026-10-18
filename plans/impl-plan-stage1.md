# План реализации Этапа 1: Foundation (Scientific Cat)

Статус: Черновик к согласованию
Дата: 2026-08-18
Связанные документы: `TODO.md` Этап 1; `FS.md`; `docs/adr/` (0001–0009)

## Цель

Собрать фундамент, на котором строится MVP: зафиксировать формат `.sdoc`
(машиночитаемо), снять технические риски формул спайками, поднять каркас
проекта и реализовать модель документа с парсером/сериализатором и тестами.

## Принципы

- **Формат — контракт:** XSD + фикстуры создаются раньше парсера.
- **Риски — рано:** два спайка (formula object, KaTeX+валидация) до UI.
- **Модель отделена от UI:** ядро тестируется без Qt-виджетов (кроме `pytest-qt` для UI-смоука).
- **Качество встроено:** ruff/mypy/pre-commit/CI с самого начала (ADR-0008).

---

## Фаза 0. Формат: XSD + фикстуры (контракт)

Вход: FS §2.4 (план XSD), ADR-0004, ADR-0007.

- [ ] 0.1 Создать `assets/schema/sdoc-v1.0.xsd` по плану FS §2.4:
  - корень `sdoc` (version/generator/created/modified);
  - `metadata`, `styles`, `body` (section/heading/paragraph/run/formula/list/table);
  - `bibliography`, `named-objects`, `resources`;
  - `xs:pattern` для ID (`p|eq|tbl|fig|sec|ref` + 5 hex) и атрибутов type/align.
- [ ] 0.2 Создать фикстуры `tests/fixtures/*.sdoc` (ADR-0007):
  - `minimal`, `cyrillic`, `formulas`, `table`, `bibliography`, `resources`.
- [ ] 0.3 Написать утилиту/тест `test_schema.py`: все фикстуры валидируются
  `lxml.etree.XMLSchema` против `sdoc-v1.0.xsd` (без сбоев).

**Выход:** формат `.sdoc` машиночитаем; фикстуры — база для round-trip и бенчмарков.

---

## Фаза 1. Технические спайки (proof-of-concept)

Вход: ADR-0001 (formula object), ADR-0002/0003 (KaTeX+pylatexenc).

- [ ] 1.1 Спайк A — inline-формула как `QTextObjectInterface`:
  - пустое окно с `QTextEdit` + регистрация объекта-формулы;
  - вставка формулы (LaTeX в `QTextCharFormat`), отрисовка, сохранение в
    `Document`, загрузка обратно → **проверка lossless round-trip**;
  - зафиксировать результат (успех/проблемы) как дополнение к ADR-0001.
- [ ] 1.2 Спайк B — рендер формул:
  - `QWebEngineView` рендерит KaTeX из локальных ассетов `assets/katex/`;
  - `pylatexenc` валидирует LaTeX (нет ложных ошибок на матрицах/окружениях);
  - проверить офлайн-работу WebEngine и кэш формул (основа ADR-0009/0014);
  - зафиксировать результат как дополнение к ADR-0002/0003.
- [ ] 1.3 Скачать/зафиксировать ассеты KaTeX (и при необходимости MathJax-svg) в `assets/`.

**Выход:** риски ADR-0001/0002/0003 сняты; решения подтверждены/скорректированы.

---

## Фаза 2. Каркас проекта (scaffold)

Вход: TODO Этап 1 §1.1–1.2; ADR-0008.

- [ ] 2.1 `pyproject.toml`: зависимости runtime (PySide6, pylatexenc, lxml,
  python-docx, mistletoe) и dev (ruff, mypy, pytest, pytest-qt, hypothesis);
  конфиг ruff/mypy; `sympy` — опциональная (ADR-0003).
- [ ] 2.2 `requirements.txt` (уровень совместимости, как в TZ §5.2).
- [ ] 2.3 Структура пакетов с `__init__.py`: `core/`, `ui/`, `services/`,
  `assets/` (icons, fonts, templates, styles, katex, schema), `tests/`.
- [ ] 2.4 `main.py` — точка входа (запуск `MainWindow`, инициализация `AppLogger`).
- [ ] 2.5 `pre-commit`-хуки, `.gitignore`, `README.md`.
- [ ] 2.6 CI (GitHub Actions): PR → `ruff check`, `mypy`, `pytest`; ночной → бенчмарки + матрица ОС.

**Выход:** репозиторий собирается и проходит линт/типы; окружение воспроизводимо.

---

## Фаза 3. Ядро: модель + парсер/сериализатор

Вход: FS §4.1–4.6; ADR-0004; ADR-0013 (задел Command-паттерна).

- [ ] 3.1 `core/formula.py` — модель `Formula` (latex/type/id/number,
  `validate()` через `pylatexenc`, `_generate_id()`).
- [ ] 3.2 `core/document.py` — `Document` + `Section`/`Paragraph`/`Run`/
  `Table`/`Styles`/`Bibliography`; `new()`, `from_file()`, `save()`,
  `get_word_count()` (без `get_page_count()` — см. ADR-0005).
- [ ] 3.3 `core/xml_parser.py` — `XMLParser` (lxml + XSD-валидация по 0.1)
  и `XMLSerializer` (`Document` → XML, генерация ID).
- [ ] 3.4 `core/formula_engine.py` — каркас `FormulaEngine` с бэкендами
  (KaTeX/matplotlib) по ADR-0002; `validate_latex()`.
- [ ] 3.5 `core/ir.py` — промежуточное представление для экспорта/превью
  (ADR-0006, ADR-0014).
- [ ] 3.6 Юнит-тесты: `test_document`, `test_xml_parser`, `test_xml_serializer`,
  `test_formula`, `test_roundtrip` (по фикстурам 0.2), `test_schema`.

**Выход:** `.sdoc` открывается/сохраняется без потерь (критерий приёмки №1);
ядро покрыто тестами.

---

## Фаза 4. UI-скелет

Вход: FS §3.1, §4.7; ADR-0001.

- [ ] 4.1 `services/logger.py` — `AppLogger` (APPDATA, ротация по дням).
- [ ] 4.2 `ui/main_window.py` — `QMainWindow`: меню (Файл/Правка/Вид/Формат/
  Вставка/Сервис/Справка), toolbar, splitter Editor↔Preview, statusbar.
- [ ] 4.3 `ui/editor_widget.py` — `EditorWidget(QTextEdit)` с регистрацией
  объекта-формулы (результат спайка 1.1).
- [ ] 4.4 `ui/preview_widget.py` — `PreviewWidget(QWebEngineView)` заглушка
  (рендер пустого документа; полный — в Этапе 2).
- [ ] 4.5 Смоук-тест `test_main_window.py` (`pytest-qt`): окно открывается,
  создание нового документа.

**Выход:** приложение запускается, окно открывается, ядро подключено.

---

## Критерии завершения Этапа 1

1. `assets/schema/sdoc-v1.0.xsd` валидирует все фикстуры.
2. Спайки A и B задокументированы (результат в ADR-0001/0002/0003).
3. `pytest` зелёный (core + ui smoke), `ruff check` и `mypy` проходят.
4. `main.py` запускает окно без ошибок.
5. Документ `.sdoc` (фикстура) открывается/сохраняется без потери данных.

---

*План Этапа 1 | Дата: 2026-08-18 | Статус: Draft для согласования*