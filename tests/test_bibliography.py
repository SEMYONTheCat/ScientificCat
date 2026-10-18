"""Тесты менеджера библиографии (см. FS §4.6, TZ §2.6)."""

from __future__ import annotations

import pytest

from core.bibliography import BibManager, parse_bibtex
from core.document import BibEntry, Bibliography

SAMPLE_BIB = """
@article{einstein1905,
  title = {О электродинамике движущихся тел},
  author = {Эйнштейн, А.},
  journal = {Annalen der Physik},
  year = {1905},
  volume = {322},
  pages = {891--921}
}
@book{bohr1913,
  title = {On the Constitution of Atoms},
  author = {Bohr, N.},
  publisher = {Nature},
  year = {1913}
}
"""


class TestBibManager:
    def test_import_bibtex(self) -> None:
        manager = BibManager()
        count = manager.import_bibtex(SAMPLE_BIB)
        assert count == 2
        assert manager.bibliography.entries[0].key == "einstein1905"

    def test_generate_bibliography_gost(self) -> None:
        manager = BibManager(Bibliography(style="GOST"))
        manager.import_bibtex(SAMPLE_BIB)
        text = manager.generate_bibliography()
        assert "Эйнштейн" in text
        assert text.count("\n") == 1  # две записи

    def test_citation_position(self) -> None:
        manager = BibManager()
        manager.import_bibtex(SAMPLE_BIB)
        cit = manager.get_citation(1)
        assert "Эйнштейн" in cit

    def test_citation_out_of_range(self) -> None:
        manager = BibManager()
        with pytest.raises(IndexError):
            manager.get_citation(5)

    def test_format_styles(self) -> None:
        entry = BibEntry(key="k", title="T", author="A", year="2020", journal="J")
        assert "A" in BibManager.format_entry(entry, "GOST", 1)
        assert "A" in BibManager.format_entry(entry, "APA", 1)
        assert "[1]" in BibManager.format_entry(entry, "IEEE", 1)

    def test_parse_bibtex(self) -> None:
        entries = parse_bibtex(SAMPLE_BIB)
        assert len(entries) == 2
        assert entries[1].entry_type == "book"