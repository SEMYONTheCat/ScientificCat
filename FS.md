Формальная Спецификация: Scientific Cat v1.0


1. Архитектура проекта
   1.1. Структура каталогов
ScientificCat/
├── main.py                      # Точка входа
├── requirements.txt
├── README.md
├── Concept.md
├── TZ.md
├── FS.md
├── TODO.md
│
├── core/
│   ├── __init__.py
│   ├── document.py              # Модель документа
│   ├── xml_parser.py            # Парсер .sdoc
│   ├── xml_serializer.py        # Сериализатор .sdoc
│   ├── formula.py               # Модель формулы (Formula)
│   ├── formula_engine.py        # Движок формул (конвейер рендеринга)
│   ├── exporter.py              # Экспорт (PDF, DOCX, HTML, LaTeX)
│   └── bibliography.py          # Менеджер библиографии
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # Главное окно (QMainWindow)
│   ├── formula_dialog.py        # Диалог WYSIWYG формул
│   ├── editor_widget.py         # Виджет редактора (QTextEdit)
│   ├── preview_widget.py        # Виджет предпросмотра (QWebEngineView)
│   ├── toolbar.py               # Панель инструментов
│   ├── status_bar.py            # Строка состояния
│   └── symbol_palette.py        # Палитра символов
│
├── assets/
│   ├── icons/                   # SVG/PNG иконки
│   ├── fonts/                   # Поддерживаемые шрифты
│   ├── templates/               # Шаблоны документов (.sdoc)
│   └── styles/                  # Qt Style Sheets
│
├── services/
│   ├── autostore.py             # Автосохранение
│   ├── undo_redo.py             # Система отмены/повтора
│   └── logger.py                # Логирование
│
└── tests/
    ├── __init__.py
    ├── test_document.py
    ├── test_xml_parser.py
    ├── test_formula_engine.py
    └── test_exporter.py
2. Формат файла .sdoc
   2.1. Схема XML-документа
<?xml version="1.0" encoding="UTF-8"?>
<sdoc version="1.0" generator="ScientificCat/1.0" created="2026-08-18T12:00:00Z" modified="2026-08-18T12:00:00Z">

    <!-- Метаданные -->
    <metadata>
        <title>Название документа</title>
        <author>Имя Фамилия</author>
        <keywords>ключ1, ключ2</keywords>
        <template>article</template>
        <language>ru</language>
    </metadata>

    <!-- Стили оформления -->
    <styles>
        <font name="Main" family="Arial" size="12" unit="pt"/>
        <font name="Formula" family="Computer Modern" size="14" unit="pt"/>
        <style name="Heading1" font="Heading" size="16" bold="true" align="left"/>
        <style name="Heading2" font="Heading" size="14" bold="true" align="left"/>
        <style name="Body" font="Main" size="12" bold="false" align="justify"/>
        <style name="Formula" font="Formula" size="12" bold="false" align="center"/>
        <margin top="20mm" bottom="20mm" left="30mm" right="20mm"/>
        <line_spacing unit="pt">20</line_spacing>
    </styles>

    <!-- Тело документа -->
    <body>

        <!-- Секция (глава, раздел) -->
        <section id="sec1" number="1">
            <heading level="1" id="h1">Введение</heading>

            <!-- Абзац -->
            <paragraph id="p1" align="justify">
                <run text="Это текст со вставленной формулой " style="Body"/>
                <formula id="eq1" type="inline" latex="E = mc^2" number="1"/>
                <run text=" и продолжается текст" style="Body"/>
            </paragraph>

            <!-- Блочная формула -->
            <formula id="eq2" type="display" latex="\int_0^\infty e^{-x} dx = 1" number="2" centered="true"/>

            <!-- Список -->
            <list type="unordered" id="list1">
                <item>Пункт первый</item>
                <item>Пункт второй</item>
                <item>Пункт третий</item>
            </list>

            <!-- Подраздел -->
            <section id="sec1.1" number="1.1">
                <heading level="2" id="h2">Описание</heading>
                <paragraph id="p2">
                    <run text="Текст подраздела" style="Body"/>
                </paragraph>
            </section>
        </section>

        <!-- Таблица -->
        <table id="tbl1" cols="3" rows="2" align="center">
            <caption>Таблица 1 — Пример таблицы</caption>
            <row>
                <cell colspan="1" rowspan="1" align="center"><run text="Заголовок 1"/></cell>
                <cell colspan="1" rowspan="1" align="center"><run text="Заголовок 2"/></cell>
                <cell colspan="1" rowspan="1" align="center"><run text="Заголовок 3"/></cell>
            </row>
            <row>
                <cell colspan="1" rowspan="1" align="center"><run text="Ячейка"/></cell>
                <cell colspan="1" rowspan="1" align="center"><formula latex="x^2"/></cell>
                <cell colspan="1" rowspan="1" align="center"><run text="Данные"/></cell>
            </row>
        </table>

    </body>

    <!-- Библиография -->
    <bibliography style="GOST">
        <citation id="ref1" key="einstein1905">
            <title>О электродинамике движущихся тел</title>
            <author>Эйнштейн А.</author>
            <journal>Annalen der Physik</journal>
            <year>1905</year>
            <volume>322</volume>
            <pages>891–921</pages>
        </citation>
        <citation id="ref2" key="bohr1913">
            <title>On the Constitution of Atoms</title>
            <author>Bohr N.</author>
            <journal>Nature</journal>
            <year>1913</year>
        </citation>
    </bibliography>

    <!-- Список именуемых объектов (для перекрёстных ссылок) -->
    <named-objects>
        <object id="eq1" type="equation" label="уравнение (1)"/>
        <object id="eq2" type="equation" label="уравнение (2)"/>
        <object id="tbl1" type="table" label="таблица 1"/>
    </named-objects>

    <!-- Вложенные ресурсы (опционально, base64) -->
    <resources>
        <resource id="img1" type="image" format="png">
            <!-- base64 data -->
        </resource>
    </resources>

</sdoc>

2.2. Правила именования ID
Правило
Формат
Пример
Абзац
p + 5-значный хеш
p7f3a1
Формула
eq + 5-значный хеш
eq2b9c4
Таблица
tbl + 5-значный хеш
tbl8d1e2
Рисунок
fig + 5-значный хеш
fig5a3f0
Раздел
sec + 5-значный хеш
sec9c2d7
Стиль цитирования
ref + ключ из BibTeX
refeinstein1905
2.3. Правила нумерации

Формулы:     последовательная (1), (2), (3)...
Таблицы:     таблица 1, таблица 2, таблица 3...
Рисунки:     рисунок 1, рисунок 2, рисунок 3...
Разделы:     1, 1.1, 1.1.1, 2, 2.1...
Заголовки:   автоот ссылки на level

2.4. План XSD-схемы sdoc-v1.0.xsd (см. ADR-0004)
Единственный источник истины формата `.sdoc` — файл `assets/schema/sdoc-v1.0.xsd`.
Охватывает элементы:

| Элемент | Тип | Обязательность | Примечание |
|---|---|---|---|
| sdoc | element | да | root, атрибуты version, generator, created, modified |
| metadata | complexType | да | title, author, keywords, template, language |
| styles | complexType | да | font*, style*, margin, line_spacing |
| body | complexType | да | section*, paragraph*, formula*, list*, table* |
| section | complexType | да | id, number; heading, вложенные section |
| paragraph | complexType | да | id, align; run*, formula* |
| run | complexType | да | text, style |
| formula | complexType | да | id, type(inline/display), latex, number |
| table | complexType | опц | cols, rows, align; caption, row/cell |
| bibliography | complexType | опц | style; citation* |
| named-objects | complexType | опц | object* (id, type, label) |
| resources | complexType | опц | resource* (base64) |

Валидация: `XMLParser._validate_schema()` через `lxml.etree.XMLSchema`.

3. Интерфейсные спецификации
   3.1. Главное окно (QMainWindow)
   3.1.1. Структура
┌────────────────────────────────────────────────────────────────┐
│  Scientific Cat — [Untitled.sdoc]                              │
├────────────────────────────────────────────────────────────────┤
│  [Файл ▼] [Правка ▼] [Вид ▼] [Формат ▼] [Вставка ▼] [Сервис ▼]│
├────────────────────────────────────────────────────────────────┤
│  📄 🖨️ 📦 | 🔤 ➡️ 📎 📊 | B I U S S | H1 H2 H3 | 📈 📷 | ↩ ↪   │
├──────────────────┬─────────────────────────────────────────────┤
│                  │                                             │
│  EditorWidget    │          PreviewPanel                       │
│  QTextEdit       │          QWebEngineView                     │
│                  │                                             │
│  [Текст документа │  [Отрендеренный документ                    │
│   с формулами...] │   с формулами...]                           │
│                  │                                             │
│                  │                                             │
├──────────────────┴─────────────────────────────────────────────┤
│  📄 Страница 1/10  |  📝 500 слов  |  📐 Формула 2  |  UTF-8  │
└────────────────────────────────────────────────────────────────┘
   3.1.2. Menu Bar (меню)
   Меню
   Пункты
   Горячие клавиши
   Файл
   Новый, Открыть..., Сохранить, Сохранить как..., Экспорт →, Печать, Выход
   Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Shift+S, Ctrl+P, Alt+F4
   Правка
   Отменить, Повторить, Вырезать, Копировать, Вставить, Найти, Заменить
   Ctrl+Z, Ctrl+Y, Ctrl+X, Ctrl+C, Ctrl+V, Ctrl+F, Ctrl+H
   Вид
   Редактор, Предпросмотр, Обе панели, Полноэкранный режим
   Ctrl+Shift+E, Ctrl+Shift+P, F11
   Формат
   Шрифт, Интервал, Отступ, Выравнивание
   —
   Вставка
   Формула, Рисунок, Таблица, Цитата, Разрыв страницы
   Ctrl+M, Ctrl+I, Ctrl+T, Ctrl+R, Ctrl+Enter
   Сервис
   Словарь, Авто-нумерация, Библиография, Шаблоны
   —
   Справка
   О программе, Документация, Проверить обновления
   —
   3.2. Диалог вставки формулы
┌────────────────────────────────────────────────────────────────┐
│  Formula Editor                                        [−][□][×]│
├────────────────────────────────────────────────────────────────┤
│  ── Шаблоны ───────────────────��─────────────────────────────  │
│  [∑] [∫] [√] [∞] [α] [β] [Δ] [π] [θ] [λ] [σ] [ω] [∂]         │
│  [a/b] [ⁿ√] [²] [₃] [fₓ] [lim] [lim→] [⊕] [⊗] [∈] [⊂]        │
│  [матрица] [таблица формул] [греческие] [символы]              │
├────────────────────────────────────────────────────────────────┤
│  LaTeX ввод:                                                     │
│  [  \frac{a+b}{c-d}                        ]                   │
│  └─────────────────── Валидация: ✓ OK ───────────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────┐    ┌──────────────────────────┐   │
│  │  Layout Grid             │    │  Live Preview (KaTeX)    │   │
│  │                          │    │                          │   │
│  │  ( a    )   [Дробь]      │    │      a+b                  │   │
│  │  \sqrt{   }   [Корень]   │    │     ──────                │   │
│  │  \begin{matrix} ...      │    │      c-d                  │   │
│  │  \end{matrix}  [Матрица] │    │                          │   │
│  │                          │    │                          │   │
│  └──────────────────────────┘    └──────────────────────────┘   │
├────────────────────────────────────────────────────────────────┤
│  Тип формулы: (•) Inline   ( ) Display    Нумерация: (•) Авто  │
├────────────────────────────────────────────────────────────────┤
│                                         [OK]  [Cancel] [Insert]│
└────────────────────────────────────────────────────────────────┘
   3.3. Палитра символов (всплывающая)
┌──────────────────────────────────────────────┐
│  Поиск: [_________________]  🔍              │
├──────────────────────────────────────────────┤
│  Греческие:                                  │
│  α β γ δ ε ζ η θ ι κ λ μ ν ξ π ρ σ τ        │
│  υ φ χ ψ ω                                  │
│  Α Β Γ Δ Ε Ζ Η Θ Ι Κ Λ Μ Ν Ξ Π Ρ Σ Τ        │
│  Υ Φ Χ Ψ Ω                                  │
├──────────────────────────────────────────────┤
│  Математические:                             │
│  ≤ ≥ ≠ ≈ ≡ ∈ ∉ ⊂ ⊃ ∪ ∩ ∅ ∀ ∃ ⇒ ⇔              │
│  ∓ ± × ÷ ⋅ ∞ ∂ ∇                              │
├──────────────────────────────────────────────┤
│  Кириллица:                                  │
│  А Б В Г Д Е Ё Ж З И Й К Л М Н О П Р С Т    │
│  У Ф Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я                  │
├──────────────────────────────────────────────┤
│                        [Закрыть]             │
└──────────────────────────────────────────────┘
4. Интерфейсы модулей (API)
   4.1. Document (core/document.py)
class Document:
    """Модель научного документа"""

    def __init__(self):
        self.title: str = ""
        self.author: str = ""
        self.styles: Styles = Styles()
        self.sections: List[Section] = []
        self.bibliography: Bibliography = Bibliography()
        self.named_objects: Dict[str, NamedObject] = {}

    # Создание и загрузка
    @classmethod
    def new(cls) -> 'Document': ...
    @classmethod
    def from_file(cls, path: str) -> 'Document': ...
    @classmethod
    def from_md(cls, path: str) -> 'Document': ...

    # Сохранение
    def save(self, path: str) -> None: ...
    def save_as(self, path: str) -> None: ...
    def to_xml(self) -> str: ...  # Сериализация в XML

    # Экспорт
    def export_pdf(self, path: str) -> None: ...
    def export_docx(self, path: str) -> None: ...
    def export_html(self, path: str) -> None: ...
    def export_latex(self, path: str) -> None: ...

    # Манипуляции
    def insert_formula(self, formula: Formula) -> None:
   4.1. Document (core/document.py) — продолжение
    def insert_formula(self, formula: Formula) -> None: ...
    def insert_text(self, text: str, style: str) -> None: ...
    def insert_table(self, table: Table) -> None: ...
    def insert_image(self, image: Image) -> None: ...

    # Манипуляции
    def undo(self) -> None: ...
    def redo(self) -> None: ...
    def get_word_count(self) -> int: ...
    def get_page_count(self) -> int: ...
   4.2. Formula (core/formula.py)
class Formula:
    """Модель математической формулы"""

    def __init__(self, latex: str, formula_type: str = "inline"):
        self.latex: str = latex
        self.type: str = formula_type  # "inline" или "display"
        self.id: str = self._generate_id()
        self.number: int = 0
        self.svg: str = ""
        self.html: str = ""

    @staticmethod
    def _generate_id() -> str: ...

    def validate(self) -> bool:
        """Проверка синтаксиса через pylatexenc (см. ADR-0003)"""
        try:
            LatexWalker(self.latex).get_latex_nodes()
            return True
        except LatexWalkerError:
            return False

    def render_svg(self) -> str:
        """Рендеринг в SVG через KaTeX (Qt WebEngine JS bridge)"""
        ...

    def render_html(self) -> str:
        """Рендеринг в HTML с KaTeX CSS"""
        ...

    @classmethod
    def from_template(cls, template_name: str) -> 'Formula': ...
   4.3. XML Parser (core/xml_parser.py)
class XMLParser:
    """Парсер формата .sdoc"""

    def __init__(self, xml_path: str):
        self.path = xml_path
        self.tree = None
        self.document = None

    def parse(self) -> Document:
        """Полный парсинг XML → Document"""
        self.tree = lxml.etree.parse(self.path)
        self._validate_schema()
        self.document = Document()
        self._parse_metadata()
        self._parse_styles()
        self._parse_body()
        self._parse_bibliography()
        return self.document

    def _validate_schema(self) -> bool: ...
    def _parse_metadata(self) -> None: ...
    def _parse_styles(self) -> None: ...
    def _parse_body(self) -> None: ...
    def _parse_section(self, element) -> Section: ...
    def _parse_paragraph(self, element) -> Paragraph: ...
    def _parse_formula(self, element) -> Formula: ...
    def _parse_table(self, element) -> Table: ...
    def _parse_bibliography(self) -> None: ...

class XMLSerializer:
    """Сериализатор Document → XML"""

    def __init__(self, document: Document, output_path: str):
        self.document = document
        self.output_path = output_path
        self.root = None

    def serialize(self) -> str: ...
    def _generate_header(self) -> str: ...
    def _serialize_metadata(self) -> Element: ...
    def _serialize_styles(self) -> Element: ...
    def _serialize_body(self) -> Element: ...
    def _serialize_section(self, section: Section) -> Element: ...
    def _serialize_formula(self, formula: Formula) -> Element: ...
    def _serialize_paragraph(self, paragraph: Paragraph) -> Element: ...

4.4. Formula Engine (core/formula_engine.py)

class FormulaEngine:
    """Движок рендеринга формул (конвейер, см. ADR-0002)"""

    def __init__(self):
        self._katex = KaTeXRenderer()            # экран / live preview
        self._svg_backend = MathJaxSvgRenderer() # экспорт PDF
        self._png_backend = MatplotlibRenderer() # экспорт DOCX

    def latex_to_html(self, latex: str) -> str:
        """LaTeX → HTML (KaTeX), для экрана и HTML-экспорта"""
        return self._katex.render(latex)

    def latex_to_svg(self, latex: str) -> str:
        """LaTeX → SVG (MathJax-svg), для экспорта PDF"""
        return self._svg_backend.render(latex)

    def latex_to_png(self, latex: str, dpi: int = 300) -> bytes:
        """LaTeX → PNG (matplotlib), для экспорта DOCX"""
        return self._png_backend.render(latex, dpi)

    def validate_latex(self, latex: str) -> Tuple[bool, str]:
        """Валидация через pylatexenc + KaTeX throwOnError (см. ADR-0003)"""
        ...

    def _download_katex(self) -> str:
        """Локальная копия KaTeX (каталог assets/)"""
        ...

4.5. Exporter (core/exporter.py)

class Exporter:
    """Система экспорта"""

    def __init__(self, document: Document):
        self.document = document

    def export_pdf(self, output_path: str) -> bool:
        """Экспорт в PDF через QPrinter"""
        printer = QPrinter(QPrinter.HighResolution)
        printer.setFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(output_path)
        # Рендеринг формул в SVG → вставка в QTextDocument
        # ...
        return True

    def export_docx(self, output_path: str) -> bool:
        """Экспорт в DOCX через python-docx"""
        from docx import Document as DocxDocument
        doc = DocxDocument()
        # Конвертация параграфов
        # Формулы → InlineShapes (PNG)
        doc.save(output_path)
        return True

    def export_html(self, output_path: str) -> bool:
        """Экспорт в HTML с KaTeX"""
        html_template = self._load_html_template()
        html_content = self._render_html_body()
        final = html_template.format(content=html_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final)
        return True

    def export_latex(self, output_path: str) -> bool:
        """Экспорт в LaTeX-файл"""
        tex_content = self._convert_to_latex()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        return True

    def _convert_to_latex(self) -> str: ...
    def _render_html_body(self) -> str: ...
    def _load_html_template(self) -> str: ...
4.6. Bibliography (core/bibliography.py)

class Bibliography:
    """Менеджер библиографии"""

    def __init__(self, style: str = "GOST"):
        self.style = style  # "GOST", "APA", "IEEE"
        self.entries: List[BibEntry] = []
        self.citations: Dict[str, BibEntry] = {}

    def import_bibtex(self, path: str) -> int:
        """Импорт BibTeX файла"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Парсинг BibTeX (ручной или через biblib)
        self.entries = self._parse_bibtex(content)
        return len(self.entries)

    def add_entry(self, entry: BibEntry) -> str:
        """Добавление записи, возврат key"""
        ...

    def get_citation(self, position: int) -> str:
        """Получение цитаты по позиции [1]"""
        return self._format_entry(self.entries[position - 1])

    def generate_bibliography(self) -> str:
        """Генерация списка литературы в стиле style"""
        return "\n".join(
            self._format_entry(entry) for entry in self.entries
        )

    def _parse_bibtex(self, content: str) -> List[BibEntry]: ...
    def _format_entry(self, entry: BibEntry) -> str: ...

class BibEntry:
    """Запись библиографии"""
    key: str
    entry_type: str  # "article", "book", "inproceedings"
    title: str
    author: str
    journal: str
    year: str
    volume: str
    pages: str
    doi: str
    url: str

4.7. MainWindow (ui/main_window.py)

class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scientific Cat")
        self.resize(1200, 800)

        self.document: Document = None
        self.undo_stack = None

        self._setup_ui()
        self._setup_actions()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Создание UI компонентов"""
        self._create_menubar()
        self._create_toolbar()
        self._create_editors()
        self._create_statusbar()

        # Splitter между Editor и Preview
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.editor_widget)
        splitter.addWidget(self.preview_widget)
        splitter.setSizes([600, 600])
        self.setCentralWidget(splitter)

    def _create_menubar(self) -> None: ...
    def _create_toolbar(self) -> None: ...
    def _create_editors(self) -> None: ...
    def _create_statusbar(self) -> None: ...

    def _setup_actions(self) -> None:
        """Подключение QAction к методам"""
        self.act_new = QAction("Новый", self)
        self.act_new.setShortcut(QKeySequence.New)
        self.act_new.triggered.connect(self._on_new)

        self.act_open = QAction("Открыть", self)
        self.act_open.setShortcut(QKeySequence.Open)
        self.act_open.triggered.connect(self._on_open)

        self.act_save = QAction("Сохранить", self)
        self.act_save.setShortcut(QKeySequence.Save)
        self.act_save.triggered.connect(self._on_save)

        self.act_export_pdf = QAction("Экспорт PDF", self)
        self.act_export_pdf.triggered.connect(self._on_export_pdf)

        self.act_insert_formula = QAction("Вставить формулу", self)
        self.act_insert_formula.setShortcut("Ctrl+M")
        self.act_insert_formula.triggered.connect(self._on_insert_formula)

    def _on_new(self) -> None: ...
    def _on_open(self) -> None: ...
    def _on_save(self) -> None: ...
    def _on_export_pdf(self) -> None: ...
    def _on_insert_formula(self) -> None: ...

4.8. Formula Dialog (ui/formula_dialog.py)

class FormulaDialog(QDialog):
    """Диалог WYSIWYG вставки формул"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Formula Editor")
        self.resize(700, 500)

        self.latex_input = QLineEdit()
        self.preview_web = QWebEngineView()
        self.symbol_grid = QGridLayout()
        self.template_buttons = {}

        self._setup_ui()
        self._load_templates()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()

        # Панель шаблонов
        templates_bar = self._create_templates_bar()
        layout.addWidget(templates_bar)

        # Поле ввода LaTeX
        latex_layout = QHBoxLayout()
        latex_layout.addWidget(QLabel("LaTeX:"))
        latex_layout.addWidget(self.latex_input)
        layout.addLayout(latex_layout)

        # Валидация и статус
        self.validation_label = QLabel()
        layout.addWidget(self.validation_label)

        # Основной контент: Grid + Preview
        content_splitter = QSplitter(Qt.Horizontal)

        # Левая часть: кнопочная сетка
        grid_frame = QFrame()
        grid_layout = QGridLayout()
        self._build_symbol_grid(grid_layout)
        grid_frame.setLayout(grid_layout)

        # Правая часть: превью
        preview_frame = QFrame()
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("Live Preview:"))
        preview_layout.addWidget(self.preview_web)
        preview_frame.setLayout(preview_layout)

        content_splitter.addWidget(grid_frame)
        content_splitter.addWidget(preview_frame)
        content_splitter.setSizes([400, 300])
        layout.addWidget(content_splitter)

        # Тип формулы
        type_group = QGroupBox("Тип формулы")
        type_layout = QHBoxLayout()
        self.radio_inline = QRadioButton("Inline (в тексте)")
        self.radio_display = QRadioButton("Display (блок)")
        self.radio_inline.setChecked(True)
        type_layout.addWidget(self.radio_inline)
        type_layout.addWidget(self.radio_display)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _build_symbol_grid(self, layout: QGridLayout) -> None:
        """Заполнение сетки кнопками символов"""
        symbols = [
            ("∑", "\\sum"), ("∫", "\\int"), ("√", "\\sqrt{}"), ("∞", "\\infty"),
            ("α", "\\alpha"), ("β", "\\beta"), ("γ", "\\gamma"), ("δ", "\\delta"),
            ("π", "\\pi"), ("θ", "\\theta"), ("λ", "\\lambda"), ("σ", "\\sigma"),
            ("Δ", "\\Delta"), ("Σ", "\\Sigma"), ("Ω", "\\Omega"), ("∂", "\\partial"),
            ("≤", "\\leq"), ("≥", "\\geq"), ("≠", "\\neq"), ("≈", "\\approx"),
            ("∈", "\\in"), ("⊂", "\\subset"), ("∪", "\\cup"), ("∩", "\\cap"),
        ]
        row, col = 0, 0
        for display, latex in symbols:
            btn = QPushButton(display)
            btn.setFixedSize(40, 40)
            btn.clicked.connect(lambda checked, l=latex: self._insert_symbol(l))
            layout.addWidget(btn, row, col)
            col += 1
            if col >= 6:
                col, row = 0, row + 1

    def _load_templates(self) -> None:
        """Загрузка шаблонов формул"""
        ...

    def _connect_signals(self) -> None:
        """Подключение сигналов"""
        self.latex_input.textChanged.connect(self._on_latex_changed)

    def _on_latex_changed(self) -> None:
        """Обработка изменения LaTeX-ввода"""
        latex = self.latex_input.text()
        if not latex.strip():
            self.validation_label.setText("")
            return
        valid, msg = FormulaEngine.validate_latex(latex)
        if valid:
            self.validation_label.setText("✓ OK")
            self.validation_label.setStyleSheet("color: green;")
            self._render_preview(latex)
        else:
            self.validation_label.setText(f"✗ {msg}")
            self.validation_label.setStyleSheet("color: red;")

    def _render_preview(self, latex: str) -> None:
        """Рендеринг превью через KaTeX"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="katex.min.css">
            <script src="katex.min.js"></script>
        </head>
        <body>
            <span id="preview">{latex}</span>
            <script>
                try {{
                    katex.render(document.getElementById('preview').textContent,
                                 document.getElementById('preview'),
                                 {{ throwOnError: false }});
                }} catch(e) {{ console.log(e); }}
            </script>
        </body>
        </html>
        """
        self.preview_web.setHtml(html)

    def _insert_symbol(self, latex: str) -> None:
        """Вставка символа в текущую позицию LaTeX-строки"""
        cursor = self.latex_input.cursorPosition()
        current = self.latex_input.text()
        self.latex_input.setText(current[:cursor] + latex + current[cursor:])
        self.latex_input.setCursorPosition(cursor + len(latex))
        self._on_latex_changed()

    def _on_ok(self) -> None:
        """Обработка кнопки OK"""
        self.accept()

    def get_latex(self) -> str:
        """Получение введённого LaTeX"""
        return self.latex_input.text()

    def get_formula_type(self) -> str:
        """Получение типа формулы"""
        return "inline" if self.radio_inline.isChecked() else "display"

4.9. Editor Widget (ui/editor_widget.py)

class EditorWidget(QTextEdit):
    """Виджет текстового редактора (см. ADR-0001)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setOpenLinks(False)
        self.document().modificationChanged.connect(self._on_modified)
        # Регистрация кастомного объекта-формулы (QTextObjectInterface)
        self._register_formula_object()

    def insert_formula(self, formula: Formula) -> None:
        """Вставка формулы как inline-объекта с сохранением LaTeX в QTextCharFormat"""
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setObjectType(FORMULA_OBJECT_TYPE)      # QTextFormat.UserObject + N
        fmt.setProperty(FORMULA_LATEX_PROP, formula.latex)
        fmt.setProperty(FORMULA_TYPE_PROP, formula.type)   # inline / display
        fmt.setProperty(FORMULA_NUMBER_PROP, formula.number)
        cursor.insertText("\ufffc", fmt)            # object replacement char

    def insert_text(self, text: str, style: str = "Body") -> None:
        """Вставка текста со стилем"""
        cursor = self.textCursor()
        cursor.insertText(text)

    def paste_from_clipboard(self) -> None:
        """Обработка вставки из буфера"""
        ...

    def _on_modified(self, modified: bool) -> None:
        """Обработка изменения документа"""
        self.setWindowModified(modified)

4.10. Preview Widget (ui/preview_widget.py)

class PreviewWidget(QWebEngineView):
    """Виджет предпросмотра HTML-документа"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = self.page().settings()
        self._settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)

    def render_document(self, document: Document) -> None:
        """Рендеринг всего документа в HTML"""
        html = self._build_html(document)
        self.setHtml(html)

    def _build_html(self, document: Document) -> str:
        html_template = """
        <!DOCTYPE html>
        <html lang="{lang}">
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <link rel="stylesheet" href="katex.min.css">
            <style>
                body {{
                    font-family: {font_family};
                    font-size: {font_size};
                    line-height: {line_spacing};
                    margin: {top_margin} {right_margin} {bottom_margin} {left_margin};
                }}
                .formula-display {{
                    text-align: center;
                    margin: 1em 0;
                }}
                h1 {{ font-size: 1.6em; }}
                h2 {{ font-size: 1.4em; }}
                h3 {{ font-size: 1.2em; }}
                table {{ border-collapse: collapse; margin: 1em auto; }}
                th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
            </style>
        </head>
        <body>
            {content}
            <script src="katex.min.js"></script>
            <script>
                document.querySelectorAll('.formula-display span').forEach(function(el) {{
                    try {{ katex.render(el.textContent, el, {{ throwOnError: false }}); }}
                    catch(e) {{ console.error(e); }}
                }});
            </script>
        </body>
        </html>
        """
        content = self._render_body(document)
        styles = document.styles
        return html_template.format(
            lang=styles.language,
            title=document.title,
            font_family=styles.font_main.family,
            font_size=styles.font_main.size,
            line_spacing=styles.line_spacing,
            top_margin=styles.margin_top,
            bottom_margin=styles.margin_bottom,
            left_margin=styles.margin_left,
            right_margin=styles.margin_right,
            content=content,
        )

    def _render_body(self, document: Document) -> str:
        """Рендеринг body документа в HTML-строку"""
        html_parts = []
        for section in document.sections:
            html_parts.append(self._render_section(section))
        return "\n".join(html_parts)

    def _render_section(self, section: Section) -> str:
        html = f'<section id="{section.id}">\n'
        for heading in section.headings:
            html += f'<h{heading.level}>{heading.text}</h{heading.level}>\n'
        for child in section.children:
            if isinstance(child, Paragraph):
                html += self._render_paragraph(child)
            elif isinstance(child, Formula):
                html += f'<div class="formula-display">{child.html}</div>'
            elif isinstance(child, Table):
                html += self._render_table(child)
        html += "</section>\n"
        return html

    def _render_paragraph(self, p: Paragraph) -> str:
        return f'<p class="para" style="text-align:{p.align}">{p.text}</p>\n'

    def _render_table(self, t: Table) -> str:
        html = f'<table id="{t.id}"><caption>{t.caption}</caption>'
        for row in t.rows:
            html += "<tr>"
            for cell in row:
                html += f"<td>{cell.text}</td>"
            html += "</tr>"
        html += "</table>\n"
        return html

5. Утилитарные функции
   5.1. Генератор ID
import hashlib
import secrets

def generate_id(prefix: str = "") -> str:
    """Генерация уникального ID с префиксом"""
    suffix = secrets.token_hex(3)  # 6 символов
    return f"{prefix}{suffix}" if prefix else suffix

5.2. Валидация LaTeX

from pylatexenc.latexwalker import LatexWalker, LatexWalkerError

def validate_latex_string(latex: str) -> Tuple[bool, str]:
    """Валидация LaTeX-строки через pylatexenc (см. ADR-0003)"""
    try:
        walker = LatexWalker(latex)
        _, _, rest = walker.get_latex_nodes()
        if rest.strip():
            return False, f"Нераспознанный остаток: {rest}"
        return True, ""
    except LatexWalkerError as e:
        return False, str(e)

5.3. Конвертация Markdown → XML

import mistletoe
from mistletoe.html_renderer import HTMLRenderer

def md_to_sdoc(md_path: str, sdoc_path: str) -> Document:
    """Конвертация Markdown-файла в ScientificCat Document"""
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    parser = mistletoe.Document(md_content)
    # Парсинг AST → Document model
    doc = Document()
    doc.title = "Converted from Markdown"
    # TODO: преобразование блоков в sdoc-элементы
    return doc

6. Система стилей (Styles)
class Font:
    family: str = "Arial"
    size: int = 12
    unit: str = "pt"

class Styles:
    font_main: Font = Font()
    font_heading: Font = Font(family="Arial", size=14, unit="pt")
    font_formula: Font = Font(family="Computer Modern", size=12, unit="pt")
    font_size_body: int = 12
    line_spacing: str = "20mm"
    margin_top: str = "20mm"
    margin_bottom: str = "20mm"
    margin_left: str = "30mm"
    margin_right: str = "20mm"
    language: str = "ru"
    align_default: str = "justify"

class ParagraphStyle:
    name: str
    font: Font
    bold: bool = False
    italic: bool = False
    underline: bool = False
    align: str = "justify"

7. Автоматическое тестирование
   7.1. Структура тестов
tests/
├── conftest.py              # общие fixtures
├── test_document.py         # Document.new(), save(), load()
├── test_xml_parser.py       # XMLParser.parse()
├── test_xml_serializer.py   # XMLSerializer.serialize()
├── test_formula.py          # Formula.validate(), render_svg()
├── test_formula_engine.py   # FormulaEngine.latex_to_svg()
├── test_exporter.py          # Exporter.export_pdf(), export_html()
└── test_bibliography.py      # Bibliography.import_bibtex()
   7.2. Ключевые тесты
# test_document.py
class TestDocument:
    def test_create_new_document(self):
        doc = Document.new()
        assert doc.title == ""
        assert len(doc.sections) == 0

    def test_save_and_load(self):
        doc = Document.new()
        doc.title = "Test"
        doc.save("test.sdoc")
        loaded = Document.from_file("test.sdoc")
        assert loaded.title == "Test"

    def test_insert_formula(self):
        doc = Document.new()
        formula = Formula(latex="E = mc^2", type="inline")
        doc.insert_formula(formula)
        assert len(doc.named_objects) == 1

    def test_word_count(self):
        doc = Document.new()
        p = Paragraph()
        p.text = "Три слова"
        doc.insert_paragraph(p)
        assert doc.get_word_count() == 3

# test_formula.py
class TestFormula:
    def test_validate_valid_latex(self):
        f = Formula(latex="x^2 + y^2 = z^2")
        assert f.validate() == True

    def test_validate_invalid_latex(self):
        f = Formula(latex="x^ + ")
        assert f.validate() == False

    def test_generate_id(self):
        f = Formula(latex="a+b")
        assert f.id.startswith("eq")

# test_xml_parser.py
class TestXMLParser:
    def test_parse_metadata(self):
        parser = XMLParser("test.sdoc")
        doc = parser.parse()
        assert doc.title != ""

    def test_parse_formula(self):
        parser = XMLParser("test.sdoc")
        doc = parser.parse()
        assert any(isinstance(child, Formula) for section in doc.sections for child in section.children)

8. Интеграция с внешними библиотеками
   8.1. KaTeX (через Qt WebEngine)
# Загрузка локальных файлов KaTeX
KATEX_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "katex")

def load_katex_resources() -> Tuple[str, str]:
    """Чтение katex.min.js и katex.min.css"""
    js_path = os.path.join(KATEX_DIR, "katex.min.js")
    css_path = os.path.join(KATEX_DIR, "katex.min.css")
    with open(js_path, 'r') as f:
        js = f.read()
    with open(css_path, 'r') as f:
        css = f.read()
    return js, css

8.2. Matplotlib (резервный рендеринг)

import matplotlib.pyplot as plt
import matplotlib.texmanager as tm

def render_latex_to_png(latex: str, dpi: int = 300) -> bytes:
    """Рендеринг формулы в PNG через matplotlib"""
    fig, ax = plt.subplots(figsize=(2, 1))
    ax.set_title(latex, fontsize=12)
    ax.axis('off')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', transparent=True)
    plt.close(fig)
    return buf.getvalue()

8.3. BibTeX парсинг

def parse_bibtex_file(path: str) -> List[Dict]:
    """Парсинг BibTeX файла в список словарей"""
    entries = []
    current_entry = {}
    in_entry = False
    brace_count = 0

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('@'):
                in_entry = True
                entry_type = line.split('{')[0].replace('@', '').lower()
                current_entry = {'type': entry_type}
            elif in_entry and '{' in line:
                brace_count += line.count('{') - line.count('}')
                key = line.split(',')[0].strip()
                current_entry['key'] = key
            elif in_entry:
                if '=' in line:
                    key, value = line.split('=', 1)
                    current_entry[key.strip()] = value.strip().strip('{}')
                brace_count -= line.count('}')
                if brace_count <= 0:
                    entries.append(current_entry)
                    in_entry = False
                    brace_count = 0

    return entries

9. Сервисные модули
   9.1. Автосохранение (services/autostore.py)
from PySide6.QtCore import QTimer

class AutoStore:
    INTERVAL = 300  # 5 минут (из user_settings.json)

    def __init__(self, document: Document, save_path: str):
        self.document = document
        self.save_path = save_path
        self.timer = QTimer()                 # GUI-поток, см. ADR-0003
        self.timer.setInterval(self.INTERVAL * 1000)
        self.timer.timeout.connect(self._auto_save)

    def start(self) -> None:
        self.timer.start()

    def _auto_save(self) -> None:
        try:
            self.document.save(self.save_path)
            self._log("Auto-saved")
        except Exception as e:
            self._log(f"Auto-save failed: {e}")

    def stop(self) -> None:
        self.timer.stop()

    def _log(self, message: str) -> None:
        ...

9.2. Undo/Redo (services/undo_redo.py)

from collections import deque

class UndoRedoStack:
    MAX_HISTORY = 100

    def __init__(self):
        self.undo_stack = deque(maxlen=self.MAX_HISTORY)
        self.redo_stack = deque(maxlen=self.MAX_HISTORY)

    def push(self, action: str, data: dict) -> None:
        self.undo_stack.append((action, data))
        self.redo_stack.clear()

    def undo(self) -> tuple:
        if not self.undo_stack:
            return None, None
        action, data = self.undo_stack.pop()
        self.redo_stack.append((action, data))
        return action, data

    def redo(self) -> tuple:
        if not self.redo_stack:
            return None, None
        action, data = self.redo_stack.pop()
        self.undo_stack.append((action, data))
        return action, data

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()

9.3. Логгер (services/logger.py)

import logging
import os
from datetime import datetime

class AppLogger:
    LOG_DIR = os.path.join(os.getenv('APPDATA', '.'), 'ScientificCat', 'logs')

    def __init__(self):
        os.makedirs(self.LOG_DIR, exist_ok=True)
        self.logger = logging.getLogger('ScientificCat')
        self.logger.setLevel(logging.DEBUG)

        # File handler
        log_file = os.path.join(self.LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)

10. Конфигурация и настройки
    10.1. user_settings.json
{
    "theme": "light",
    "language": "ru",
    "font_family": "Arial",
    "font_size": 12,
    "auto_save_interval": 300,
    "recent_files": [
        "/path/to/doc1.sdoc",
        "/path/to/doc2.sdoc"
    ],
    "window": {
        "width": 1200,
        "height": 800,
        "splitter_ratio": 0.5
    },
    "export": {
        "default_format": "pdf",
        "pdf_dpi": 300
    }
}
    10.2. Шаблоны документов
    Каждый шаблон — это готовый .sdoc файл в assets/templates/:
assets/templates/
├── article.sdoc           # Научная статья
├── thesis.sdoc            # Диссертация
├── report.sdoc            # Отчёт
├── lecture.sdoc           # Лекция/конспект
└── review.sdoc            # Рецензия
11. Критерии приёмки по модулям
    Модуль
    Критерий
    Тест
    document.py
    Создание, сохранение, загрузка
    pytest tests/test_document.py
    xml_parser.py
    Парсинг любого валидного .sdoc
    pytest tests/test_xml_parser.py
    formula.py
    Валидация LaTeX, генерация ID
    pytest tests/test_formula.py
    formula_engine.py
    Рендеринг формулы в SVG
    pytest tests/test_formula_engine.py
    exporter.py
    Экспорт в PDF/HTML/LaTeX
    pytest tests/test_exporter.py
    main_window.py
    Запуск окна без ошибок
    Интеграционный тест
    formula_dialog.py
    Вставка формулы через UI
    Интеграционный тест
    Весь проект
    Сборка PyInstaller
    pyinstaller scitype.spec


12. Версионирование и распространение
    Версия
    Дата
    Изменения
    0.1.0
    TBD
    Alpha: Core XML + Editor + Basic Formula
    0.5.0
    TBD
    Alpha+: Formula Dialog + Preview + PDF
    1.0.0
    TBD
    Beta: Полный цикл, экспорт, библиография
    1.1.0
    TBD
    Templates + Polish
    2.0.0
    TBD
    Release: Cross-platform, CI/CD


Формальная Спецификация Scientific Cat v1.0 | Дата: 2026-08-18 | Статус: Draft


