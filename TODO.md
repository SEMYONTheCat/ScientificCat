# TODO: Scientific Cat v1.0

---

## Этап 1: Foundation (Недели 1–2)

### 1.1. Настройка проекта
- [ ] Инициализация Git-репозитория
- [ ] Создание `requirements.txt` (PySide6, mistletoe, sympy, pylatexenc, lxml, python-docx)
- [ ] Создание `pyproject.toml` / `setup.py`
- [ ] Настройка виртуального окружения (`venv`)
- [ ] Настройка линтера (`flake8` / `ruff`) и форматировщика (`black`)
- [ ] Настройка CI (GitHub Actions / GitLab CI): pytest + lint

### 1.2. Структура каталогов
- [ ] Создать структуру (согласно FS.md §1.1):
  ScientificCat/ ├── main.py ├── core/ ├── ui/ ├── assets/ ├── services/ └── tests/
- [ ] Добавить `__init__.py` в каждый модуль
- [ ] Создать `README.md`

### 1.3. Core: XML Format
- [ ] Реализовать класс `Document` (`core/document.py`):
  - [ ] `Document.new()` — создание пустого документа
  - [ ] `Document.save(path)` — сохранение в .sdoc
  - [ ] `Document.from_file(path)` — загрузка из .sdoc
  - [ ] `Document.insert_formula()`, `insert_text()`, `insert_table()`
  - [ ] `Document.get_word_count()`, `get_page_count()`
- [ ] Реализовать `XMLParser` (`core/xml_parser.py`):
  - [ ] Парсинг `<metadata>`, `<styles>`, `<body>`, `<bibliography>`
  - [ ] Валидация XML через XSD-схему
- [ ] Реализовать `XMLSerializer` (`core/xml_serializer.py`):
  - [ ] Сериализация `Document` → XML
  - [ ] Генерация уникальных ID (функция `generate_id()`)
- [ ] Написать тесты: `test_document.py`, `test_xml_parser.py`, `test_xml_serializer.py`
- [ ] Добавить XSD-схему в `assets/schema/sdoc-v1.0.xsd`

### 1.4. UI: Main Window Skeleton
- [ ] Реализовать `MainWindow` (`ui/main_window.py`):
  - [ ] QMainWindow с menu bar (Файл, Правка, Вид, Формат, Вставка, Сервис, Справка)
  - [ ] Toolbar с основными кнопками
  - [ ] Splitter: Editor ↔ Preview
  - [ ] Status bar (zoom, страница, слова, кодировка)
- [ ] Подключить горячие клавиши (Ctrl+N, O, S, P, M)
- [ ] `main.py`: запуск `MainWindow`, инициализация logger

---

## Этап 2: Text Editor (Недели 3–5)

### 2.1. Editor Widget
- [ ] Реализовать `EditorWidget` (`ui/editor_widget.py`) на базе `QTextBrowser`:
  - [ ] Базовое форматирование: Bold, Italic, Underline, Subscript, Superscript
  - [ ] Заголовки H1–H6
  - [ ] Списки (упорядоченные / неупорядоченные)
  - [ ] Цитаты (блочные)
  - [ ] Таблицы (до 20×20)
  - [ ] Выравнивание (left/center/right/justify)
- [ ] Markdown support:
  - [ ] Импорт `.md` через `mistletoe` → конвертация в Document
  - [ ] Экспорт `.sdoc` → `.md`

### 2.2. Preview Widget
- [ ] Реализовать `PreviewWidget` (`ui/preview_widget.py`) на базе `QWebEngineView`:
  - [ ] Рендеринг HTML-версии документа
  - [ ] Подключение KaTeX CSS/JS
  - [ ] Живое обновление при изменении Editor

### 2.3. Стилизация
- [ ] Qt Style Sheets (тёмная / светлая тема)
- [ ] Сохранение настроек (`user_settings.json`)
- [ ] Восстановление настроек при запуске

### 2.4. Автосохранение и Recovery
- [ ] Реализовать `AutoStore` (`services/autostore.py`):
  - [ ] Таймер каждые 5 минут
  - [ ] Сохранение в `.sdoc` + backup `.sdoc.backup`
- [ ] Crash-recovery: восстановление из backup при запуске

---

## Этап 3: Formula Engine (Недели 6–8)

### 3.1. Formula Model
- [ ] Реализовать класс `Formula` (`core/formula.py`):
  - [ ] `validate()` — проверка через `sympy.parsing.latex`
  - [ ] `render_svg()` — вызов KaTeX
  - [ ] `render_html()` — HTML-спан с KaTeX
  - [ ] `_generate_id()` — генерация `eqXXXXXXXX`
- [ ] Шаблоны формул: дроби, корни, интегралы, суммы, матрицы, греческие буквы

### 3.2. Formula Dialog (WYSIWYG)
- [ ] Реализовать `FormulaDialog` (`ui/formula_dialog.py`):
  - [ ] Панель шаблонов (кнопки Grid)
  - [ ] Поле ввода LaTeX с live-валидацией
  - [ ] Live Preview (`QWebEngineView` + KaTeX)
  - [ ] Radio-кнопки: Inline / Display
  - [ ] Кнопки: OK, Cancel, Insert
- [ ] Подключить к `MainWindow` (Ctrl+M)

### 3.3. Symbol Palette
- [ ] Реализовать `SymbolPalette` (`ui/symbol_palette.py`):
  - [ ] Поиск по символам
  - [ ] Вкладки: Греческие, Математические, Кириллица, Спецсимволы
  - [ ] Вставка символа в текущую позицию курсора

### 3.4. Интеграция формул с Editor
- [ ] `EditorWidget.insert_formula()` — вставка формулы в курсор
  - [ ] Inline: `<span class="katex">...</span>`
  - [ ] Display: блок с выравниванием по центру
- [ ] `PreviewWidget` рендерит формулы через KaTeX
- [ ] Сохранение/загрузка формул в `.sdoc`

### 3.5. Formula Engine (рендеринг)
- [ ] Реализовать `FormulaEngine` (`core/formula_engine.py`):
  - [ ] `latex_to_svg()` — через KaTeX (Qt WebEngine JS bridge)
  - [ ] `latex_to_image(dpi=300)` — через matplotlib (резерв)
  - [ ] `validate_latex()` — валидация + сообщение об ошибке
- [ ] Скачать KaTeX в `assets/katex/`
- [ ] Написать тесты: `test_formula.py`, `test_formula_engine.py`

---

## Этап 4: Export & Bibliography (Недели 9–11)

### 4.1. Export System
- [ ] Реализовать `Exporter` (`core/exporter.py`):
  - [ ] **PDF**: `QPrinter` → форматирование текста + формулы (SVG/рэндеринг)
  - [ ] **DOCX**: `python-docx` + вставка формул как PNG
  - [ ] **HTML**: генерация HTML с KaTeX CDN
  - [ ] **LaTeX**: конвертация `.sdoc` → `.tex` (с пакетом `amsmath`)
- [ ] Экспорт-диалог: выбор формата, настройка DPI, путей
- [ ] Написать тесты: `test_exporter.py`

### 4.2. Bibliography Manager
- [ ] Реализовать `Bibliography` (`core/bibliography.py`):
  - [ ] Импорт BibTeX (`.bib`) файлов
  - [ ] Вставка цитат `[1]`, `[2]` в текст
  - [ ] Авто-нумерация цитирований
  - [ ] Генерация списка литературы (стиль: GOST, APA, IEEE)
- [ ] Менеджер BibTeX (UI в `ui/`):
  - [ ] Просмотр/редактирование записей
  - [ ] Импорт/экспорт `.bib`
  - [ ] Поиск по записям

### 4.3. Templates
- [ ] Создать шаблоны в `assets/templates/`:
  - [ ] `article.sdoc` — научная статья
  - [ ] `thesis.sdoc` — диссертация
  - [ ] `report.sdoc` — отчёт
  - [ ] `lecture.sdoc` — лекция/конспект
  - [ ] `review.sdoc` — рецензия
- [ ] Диалог выбора шаблона при создании нового документа

---

## Этап 5: Polish & Testing (Недели 12–14)

### 5.1. Undo/Redo
- [ ] Реализовать `UndoRedoStack` (`services/undo_redo.py`)
- [ ] Подключить к Editor и Formula Dialog
- [ ] Меню Правка → Отменить / Повторить (Ctrl+Z / Ctrl+Y)

### 5.2. Navigation Panel
- [ ] Боковая панель с оглавлением (из заголовков H1–H6)
- [ ] Клик по заголовку → переход к соответствующему разделу
- [ ] Обновление при изменении структуры документа

### 5.3. Search & Replace
- [ ] Диалог поиска (Ctrl+F) и замены (Ctrl+H)
- [ ] Поиск по тексту и формулам
- [ ] Учёт регистра (опционально)

### 5.4. Cross-references
- [ ] Вставка перекрёстных ссылок: "см. уравнение (2)"
- [ ] Авто-обновление номеров формул/таблиц/рисунков
- [ ] Авто-нумерация разделов

### 5.5. Testing
- [ ] Написать интеграционные тесты:
  - [ ] `test_main_window.py` — запуск окна, создание нового документа
  - [ ] `test_formula_dialog.py` — вставка формулы через UI
  - [ ] `test_export_integration.py` — полный цикл: создание → сохранение → экспорт
- [ ] Покрыть тестами все публичные методы модулей (> 80% coverage)
- [ ] Написать smoke-тесты для каждого формата экспорта

### 5.6. Logging & Error Handling
- [ ] Настроить `AppLogger` (`services/logger.py`):
  - [ ] Логирование всех операций (загрузка, сохранение, экспорт)
  - [ ] Обработка ошибок парсинга с выводом в лог
  - [ ] Диалог критических ошибок с кодом
- [ ] Crash-dump: сохранение дапа при падении

---

## Этап 6: Packaging & Release (Недели 15–16)

### 6.1. PyInstaller
- [ ] Создать `.spec` файл для PyInstaller
- [ ] Сборка:
  - [ ] Windows: `ScientificCat.exe`
  - [ ] macOS: `ScientificCat.app`
  - [ ] Linux: `ScientificCat.AppImage` / `.deb`
- [ ] Встраивание иконок, шрифтов, KaTeX-ресурсов
- [ ] Тестирование собранных версий на чистых системах

### 6.2. Documentation
- [ ] README.md (установка, запуск, примеры)
- [ ] User Guide (инструкция по использованию)
- [ ] Developer Guide (архитектура, API)
- [ ] CHANGELOG.md

### 6.3. Release
- [ ] Версионирование по SemVer (1.0.0)
- [ ] Создание release на GitHub/GitLab
- [ ] Публикация артефактов (exe, app, appimage)
- [ ] Сбор обратной связи от тестовых пользователей

---

## Этап 7: Future Enhancements (Post-v1.0)

- [ ] **Real-time collaboration** — синхронное редактирование
- [ ] **Plugin system** — расширение функционала через плагины
- [ ] **Voice input** — диктовка текста (Speech-to-Text)
- [ ] **Graph editor** — вставка графиков и диаграмм
- [ ] **LaTeX preview in editor** — рендеринг формул прямо в QTextBrowser
- [ ] **Mobile companion** — просмотр документов через QR-код
- [ ] **Cloud sync** — интеграция с облачными хранилищами
- [ ] **AI-assisted** — автодополнение формул, проверка стиля
- [ ] **Equation OCR** — распознавание формул с фотографий
- [ ] **Version control** — интеграция с Git для `.sdoc` файлов

---

## Сводная таблица задач

| Этап | Задач | Дедлайн | Статус |
|---|---|---|---|
| 1. Foundation | 15 | Неделя 2 | ⬜ |
| 2. Text Editor | 18 | Неделя 5 | ⬜ |
| 3. Formula Engine | 20 | Неделя 8 | ⬜ |
| 4. Export & Bibliography | 15 | Неделя 11 | ⬜ |
| 5. Polish & Testing | 22 | Неделя 14 | ⬜ |
| 6. Packaging & Release | 8 | Неделя 16 | ⬜ |
| **Итого** | **98** | **4 месяца** | |

---

*TODO Scientific Cat v1.0 | Дата: 2026-08-18 | Статус: Draft*

