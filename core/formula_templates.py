"""Шаблоны формул и наборы символов (см. FS §3.2, §3.3, TZ Фр-02/Фр-03).

Используются WYSIWYG-диалогом формул и палитрой символов.
"""

from __future__ import annotations

# Шаблоны формул: имя → LaTeX-заготовка (курсор встаёт после фрагмента)
FORMULA_TEMPLATES: dict[str, str] = {
    "Дробь": r"\frac{}{}",
    "Корень": r"\sqrt{}",
    "Корень n": r"\sqrt[n]{}",
    "Интеграл": r"\int_{}^{} dx",
    "Сумма": r"\sum_{i=1}^{n}",
    "Произведение": r"\prod_{i=1}^{n}",
    "Предел": r"\lim_{x \to \infty}",
    "Матрица": r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
    "Вектор": r"\vec{}",
    "Черта": r"\overline{}",
}

# Греческие буквы: отображаемое имя → LaTeX
GREEK_SYMBOLS: list[tuple[str, str]] = [
    ("α", r"\alpha"), ("β", r"\beta"), ("γ", r"\gamma"), ("δ", r"\delta"),
    ("ε", r"\varepsilon"), ("ζ", r"\zeta"), ("η", r"\eta"), ("θ", r"\theta"),
    ("λ", r"\lambda"), ("μ", r"\mu"), ("ν", r"\nu"), ("ξ", r"\xi"),
    ("π", r"\pi"), ("ρ", r"\rho"), ("σ", r"\sigma"), ("τ", r"\tau"),
    ("φ", r"\phi"), ("χ", r"\chi"), ("ψ", r"\psi"), ("ω", r"\omega"),
    ("Γ", r"\Gamma"), ("Δ", r"\Delta"), ("Θ", r"\Theta"), ("Λ", r"\Lambda"),
    ("Σ", r"\Sigma"), ("Φ", r"\Phi"), ("Ψ", r"\Psi"), ("Ω", r"\Omega"),
]

# Математические символы
MATH_SYMBOLS: list[tuple[str, str]] = [
    ("≤", r"\leq"), ("≥", r"\geq"), ("≠", r"\neq"), ("≈", r"\approx"),
    ("≡", r"\equiv"), ("∈", r"\in"), ("∉", r"\notin"), ("⊂", r"\subset"),
    ("∪", r"\cup"), ("∩", r"\cap"), ("∅", r"\emptyset"), ("∀", r"\forall"),
    ("∃", r"\exists"), ("⇒", r"\Rightarrow"), ("⇔", r"\Leftrightarrow"),
    ("∞", r"\infty"), ("∂", r"\partial"), ("∇", r"\nabla"), ("±", r"\pm"),
    ("×", r"\times"), ("÷", r"\div"), ("⋅", r"\cdot"), ("∑", r"\sum"),
    ("∫", r"\int"), ("∏", r"\prod"), ("√", r"\sqrt{}"), ("→", r"\to"),
]

# Специальные символы
SPECIAL_SYMBOLS: list[tuple[str, str]] = [
    ("°", r"^{\circ}"), ("Å", r"\AA"), ("‰", r"\permil"),
    ("†", r"\dagger"), ("‡", r"\ddagger"), ("#", r"\#"),
    ("&", r"\&"), ("%", r"\%"), ("_", r"\_"),
]

# Кириллица (для ввода в текст формул)
CYRILLIC_LETTERS: str = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"