# Руководство разработчика Scientific Cat

Архитектура, конвейеры данных, сборка и качество. Все решения фиксируются в
[`docs/adr/`](adr/) (Architecture Decision Records).

## 1. Стек и структура

| Слой | Ответственность | Ключевые файлы |
|---|---|---|
| `core/` | Модель, `.sdoc`, формулы, экспорт, библиография, ссылки, IR | `document.py`, `xml_parser.py`, `xml_serializer.py`, `formula.py`, `formula_engine.py`, `exporter.py`, `bibliography.py`, `references.py`, `ir.py` |
| `ui/` | Qt-интерфейс | `main_window.py`, `editor_widget.py`, `preview_widget.py`, `formula_dialog.py`, `symbol_palette.py`, `export_dialog.py`, `find_replace_dialog.py`, `navigation_panel.py` |
| `services/` | Сквозные сервисы | `autostore.py`, `undo_redo.py`, `settings.py`, `logger.py`, `paths.py` |
| `assets/` | XSD, стили, шаблоны, KaTeX | `schema/`, `styles/`, `templates/`, `katex/` |
| `tests/` | Тесты и фикстуры | `fixtures/*.sdoc`, `test_*.py` |

## 2. Основные конвейеры

### 2.1. Формат `.sdoc` (ADR-0004/0005)

- **XMLSerializer** (`Document → XML`) и **XMLParser** (`XML → Document`).
- Валидация через XSD (`assets/schema/sdoc-v1.0.xsd`) средствами `lxml`.
- Каждый элемент `id` обязан соответствовать XSD-паттерну
  `[a-zA-Z][a-zA-Z0-9_\-.]{2,31}` (минимум 3 символа).

### 2.2. Рендеринг и превью (ADR-0002/0014)

- `Document → IR → HTML` → KaTeX (локальные ассеты `assets/katex/`).
- Live-превью с дебаунсингом (`QTimer`, 300 мс) в `MainWindow`.

### 2.3. Экспорт (ADR-0006)

- Единый конвейер `Document → IR → формат` в `core/exporter.py`:
  LaTeX / HTML / DOCX (`python-docx`, формулы PNG через matplotlib) / PDF (`QPrinter`).

### 2.4. Undo/Redo (ADR-0013)

- Command-паттерн на уровне модели: `services/undo_redo.py`
  (`InsertParagraph`, `RemoveBlock`, `UndoRedoStack`, MAX_HISTORY=100).
- Редактор использует нативный undo/redo QTextEdit; модель-стек покрыт тестами.

### 2.5. Ссылки (ADR-0011)

- `core/references.py` (`ReferenceResolver`): авто-нумерация разделов/формул,
  регистрация `named_objects`, разрешение «уравнение (N)».

## 3. Валидация формул (ADR-0003)

- Быстрая структурная проверка — `pylatexenc`.
- Авторитетная проверка полноты — KaTeX (`throwOnError`), выполняется в UI.

## 4. Headless / CI

QtWebEngine падает при завершении процесса в offscreen-режиме, поэтому при
`QT_QPA_PLATFORM=offscreen` `MainWindow` и `FormulaDialog` используют
плейсхолдеры (`QWidget`/`QLabel`) вместо `QWebEngineView`.

## 5. Качество

```bat
.venv\Scripts\python.exe -m ruff check .      :: линт
.venv\Scripts\python.exe -m mypy core          :: strict-типизация ядра
.venv\Scripts\python.exe -m pytest             :: тесты
setup_env.bat --check                          :: полный прогон
```

- `mypy` strict для `core/` и `services/` (исключены `ui/`, `core/markdown.py`).
- Покрытие публичных методов — см. интеграционные и smoke-тесты
  (`test_export_integration.py`, `test_main_window.py`, `test_formula_dialog.py`).

## 6. Ресурсы и PyInstaller

Приложение читает ресурсы через `services.paths.resource_path()`, что
корректно работает и в frozen-режиме (`sys._MEIPASS`).

### 6.1. Сборка CLI-скриптами

```bat
build.bat        :: Windows
./build.sh       :: Linux/macOS
```

Скрипты вызывают PyInstaller с `--add-data` для `assets/styles`,
`assets/schema`, `assets/katex`, `assets/templates` и `icons`.

### 6.2. Эквивалент `.spec` (для ручной сборки)

Если требуется спецификация `.spec`, её содержимое (аналог того, что делают
build-скрипты):

```python
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ("assets/styles", "assets/styles"),
    ("assets/schema", "assets/schema"),
    ("assets/katex", "assets/katex"),
    ("assets/templates", "assets/templates"),
    ("icons", "icons"),
]
datas += collect_data_files("matplotlib")

hiddenimports = [
    "lxml._elementpath",
    "mistletoe.span_token",
    "mistletoe.block_token",
    "matplotlib.backends.backend_agg",
]
```

Замечания:
- Preview и формульный диалог требуют **QtWebEngine** — не исключайте его.
- PNG-экспорт (DOCX) требует **matplotlib** — включите его данные/hiddenimports.
- Для иконки Windows сконвертируйте `icons/icon.png` в `icons/icon.ico` и
  добавьте `--icon "icons/icon.ico"`.

## 7. Логирование и отказы

- `services/logger.py` — логи в `%APPDATA%/ScientificCat/logs/`.
- Crash-дампы — в `%APPDATA%/ScientificCat/crashes/` через `sys.excepthook`
  (настраивается в `main.py`).

## 8. Версионирование

SemVer. Единственный источник версии — `pyproject.toml`
(`project.version = "1.0.0"`); дублируется в `core/__init__.py::__version__`.