# Changelog

Все значимые изменения проекта документируются в этом файле.
Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии — [SemVer](https://semver.org/lang/ru/).

## [Unreleased]

### Добавлено
- **WYSIWYG-рендер формул в редакторе** (TODO §7): формулы отображаются
  прямо в `QTextEdit` как изображения (LaTeX → PNG через matplotlib,
  ADR-0002) с кэшированием; при отсутствии matplotlib — фолбэк на плейсхолдер.
  Реализовано через `QTextObjectInterface` ([`ui/editor_widget.py`](ui/editor_widget.py)).
- **Строка состояния**: слова, формулы, позиция курсора (строка/колонка),
  зум, оценка числа страниц, кодировка, текущая тема; обновляется в реальном
  времени.
- **Иконки кнопок** из Unicode-глифов (📂 💾 ∑ 🔍 …) для всех действий
  меню/тулбара ([`ui/main_window.py`](ui/main_window.py)).
- **Масштабирование окон**: окно по умолчанию 1500×950 (мин. 1000×650),
  базовый зум редактора 110%, Ctrl+=/Ctrl+-/Ctrl+0 и Ctrl+колесо мыши
  изменяют масштаб; размер формул увеличен.

## [1.0.0] — 2026-08-19

### Добавлено
- **Этап 1 (Foundation):** модель `Document`, парсер/сериализатор `.sdoc`,
  XSD-схема, 6 эталонных фикстуры, spikes (формула-объект, KaTeX), scaffold
  (pyproject, CI, pre-commit, `setup_env.bat`).
- **Этап 2 (Text Editor):** `EditorWidget` (форматирование, заголовки, списки,
  выравнивание), live-превью KaTeX, темы QSS, настройки, автосохранение и recovery.
- **Этап 3 (Formula Engine):** модель/движок формул, WYSIWYG-диалог (Ctrl+M),
  палитра символов, шаблоны формул.
- **Этап 4 (Export & Bibliography):** `Exporter` (PDF/DOCX/HTML/LaTeX через IR),
  `BibManager` (импорт BibTeX, GOST/APA/IEEE), диалог экспорта, 5 шаблонов документов.
- **Этап 5 (Polish & Testing):** undo/redo (ADR-0013), панель навигации,
  поиск и замена (Ctrl+F/Ctrl+H), перекрёстные ссылки (ADR-0011),
  логирование и crash-дампы, интеграционные тесты.
- **Этап 6 (Packaging):** build-скрипты PyInstaller (`build.bat`, `build.sh`),
  `services/paths.py` для frozen-режима, README, User/Developer Guide.

### Изменено
- Версия проекта поднята до `1.0.0` (SemVer).

### Исправлено
- Обратный слэш в f-string (несовместим с Python 3.10).
- Иерархическая авто-нумерация разделов (1, 1.1, 1.1.1…).
- XSD-валидация `id` элементов (минимум 3 символа).

[1.0.0]: https://example.com/scientific-cat/tree/v1.0.0