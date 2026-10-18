"""Менеджер библиографии (см. FS §4.6, TZ §2.6, ADR-0011).

Импорт BibTeX, вставка цитат, автоперенумерация и генерация списка
литературы по стилям GOST / APA / IEEE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.document import BibEntry, Bibliography


@dataclass
class BibManager:
    """Работа с библиографией документа."""

    bibliography: Bibliography = field(default_factory=Bibliography)

    def import_bibtex(self, text: str) -> int:
        """Парсинг BibTeX-текста и добавление записей в Bibliography."""
        entries = parse_bibtex(text)
        self.bibliography.entries.extend(entries)
        return len(entries)

    def get_citation(self, position: int) -> str:
        """Цитата по позиции в стиле bibliography.style."""
        if position < 1 or position > len(self.bibliography.entries):
            raise IndexError("Позиция цитаты вне диапазона")
        entry = self.bibliography.entries[position - 1]
        return self.format_entry(entry, self.bibliography.style, number=position)

    def generate_bibliography(self) -> str:
        """Полный список литературы в текущем стиле."""
        lines = [
            self.format_entry(entry, self.bibliography.style, number=i)
            for i, entry in enumerate(self.bibliography.entries, start=1)
        ]
        return "\n".join(lines)

    def export_bibtex(self) -> str:
        """Экспорт всех записей библиографии в строку BibTeX."""
        return entries_to_bibtex(self.bibliography.entries)

    @staticmethod
    def format_entry(entry: BibEntry, style: str, number: int = 0) -> str:
        """Форматирование одной записи по стилю."""
        formatter = _FORMATTERS.get(style, _FORMATTERS["GOST"])
        return formatter(entry, number)


# ---------- Форматтеры ----------


def _gost(entry: BibEntry, number: int) -> str:
    author = entry.author or entry.publisher or ""
    title = entry.title or ""
    year = entry.year or ""
    source = entry.journal or entry.booktitle or entry.publisher or ""
    parts = [p for p in (author, title, source, year) if p]
    body = ". ".join(parts)
    return f"{number}. {body}."


def _apa(entry: BibEntry, number: int) -> str:
    author = entry.author or entry.publisher or ""
    year = f"({entry.year})" if entry.year else ""
    title = entry.title or ""
    source = entry.journal or entry.booktitle or ""
    parts = [p for p in (author, year, title, source) if p]
    return ". ".join(parts) + "."


def _ieee(entry: BibEntry, number: int) -> str:
    author = entry.author or entry.publisher or ""
    title = entry.title or ""
    year = entry.year or ""
    source = entry.journal or entry.booktitle or ""
    bits = [b for b in (author, f"“{title}”" if title else "", source, year) if b]
    return f"[{number}] {', '.join(bits)}."


_FORMATTERS = {"GOST": _gost, "APA": _apa, "IEEE": _ieee}


# ---------- BibTeX-парсер ----------


def parse_bibtex(text: str) -> list[BibEntry]:
    """Парсер BibTeX со сбалансированным разбором фигурных скобок."""
    entries: list[BibEntry] = []
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,{}]+)\s*,")
    for match in pattern.finditer(text):
        entry_type = match.group(1).lower()
        key = match.group(2).strip()
        body = _balanced_body(text, match.end())
        fields = _parse_fields(body)
        entries.append(
            BibEntry(
                key=key,
                entry_type=entry_type,
                title=fields.get("title", ""),
                author=fields.get("author", ""),
                journal=fields.get("journal", ""),
                booktitle=fields.get("booktitle", ""),
                year=fields.get("year", ""),
                volume=fields.get("volume", ""),
                number=fields.get("number", ""),
                pages=fields.get("pages", ""),
                publisher=fields.get("publisher", ""),
                address=fields.get("address", ""),
                doi=fields.get("doi", ""),
                url=fields.get("url", ""),
            )
        )
    return entries


def _balanced_body(text: str, start: int) -> str:
    """Вернуть содержимое тела записи до сбалансированной закрывающей скобки."""
    depth = 1
    j = start
    while j < len(text) and depth:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[start : j - 1]


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    pattern = re.compile(r"(\w+)\s*=\s*(\{[^{}]*\}|\"[^\"]*\"|[^\s,]+)")
    for match in pattern.finditer(body):
        name = match.group(1).lower()
        value = match.group(2).strip().strip("{}").strip('"')
        fields[name] = value
    return fields


def entries_to_bibtex(entries: list[BibEntry]) -> str:
    """Сериализовать список записей BibEntry в строку формата BibTeX."""
    blocks: list[str] = []
    for entry in entries:
        kind = entry.entry_type or "article"
        lines = [f"@{kind}{{{entry.key},"]
        fields = [
            ("title", entry.title),
            ("author", entry.author),
            ("journal", entry.journal),
            ("booktitle", entry.booktitle),
            ("year", entry.year),
            ("volume", entry.volume),
            ("number", entry.number),
            ("pages", entry.pages),
            ("publisher", entry.publisher),
            ("address", entry.address),
            ("doi", entry.doi),
            ("url", entry.url),
        ]
        for name, value in fields:
            if value:
                lines.append(f"  {name} = {{{value}}},")
        lines.append("}\n")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)
