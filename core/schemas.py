from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Author:
    full_name: str = ""
    initials_name: str = ""
    email: str = ""
    affiliation: str = ""
    is_corresponding: bool = False


@dataclass
class Abstract:
    ru: str = ""
    en: str = ""


@dataclass
class Keywords:
    ru: list[str] = field(default_factory=list)
    en: list[str] = field(default_factory=list)


@dataclass
class Section:
    level: int = 1
    title: str = ""
    text: str = ""


@dataclass
class Figure:
    number: int = 0
    caption: str = ""


@dataclass
class Reference:
    number: int = 0
    raw_text: str = ""


@dataclass
class ArticleData:
    title_ru: str = ""
    title_en: str = ""

    udc: str = ""
    doi: str = ""

    authors: list[Author] = field(default_factory=list)

    abstract: Abstract = field(default_factory=Abstract)
    keywords: Keywords = field(default_factory=Keywords)

    sections: list[Section] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)

    funding: str = ""
    acknowledgements: str = ""

    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": {"ru": self.title_ru, "en": self.title_en},
            "udc": self.udc,
            "doi": self.doi,
            "authors": [
                {
                    "full_name": a.full_name,
                    "initials_name": a.initials_name,
                    "email": a.email,
                    "affiliation": a.affiliation,
                    "is_corresponding": a.is_corresponding,
                }
                for a in self.authors
            ],
            "abstract": {"ru": self.abstract.ru, "en": self.abstract.en},
            "keywords": {"ru": self.keywords.ru, "en": self.keywords.en},
            "sections": [
                {"level": s.level, "title": s.title, "text": s.text[:200] + "..."}
                for s in self.sections
            ],
            "figures": [{"number": f.number, "caption": f.caption} for f in self.figures],
            "references": [{"number": r.number, "text": r.raw_text} for r in self.references],
            "funding": self.funding,
            "acknowledgements": self.acknowledgements,
            "warnings": self.warnings,
        }