from dataclasses import dataclass, field
from typing import Optional

from dataclasses import dataclass, field


@dataclass
class Affiliation:
    id: int = 0
    name: str = ""
    city: str = ""
    country: str = ""


@dataclass
class Author:
    full_name: str = ""
    initials_name: str = ""
    email: str = ""
    orcid: str = ""
    affiliations: list[int] = field(default_factory=list)
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
class Block:
    type: str = "paragraph"
    text: str = ""


@dataclass
class Section:
    level: int = 1
    title: str = ""
    blocks: list[Block] = field(default_factory=list)


@dataclass
class Figure:
    number: int = 0
    caption: str = ""
    image_path: str = ""
    anchor_text: str = ""


@dataclass
class Table:
    number: int = 0
    caption: str = ""
    data: list = field(default_factory=list)
    anchor_text: str = ""


@dataclass
class Equation:
    number: int = 0
    omml: str = ""
    latex: str = ""
    text: str = ""


@dataclass
class Reference:
    number: int = 0
    raw_text: str = ""
    doi: str = ""
    url: str = ""


@dataclass
class ArticleData:
    title_ru: str = ""
    title_en: str = ""

    udc: str = ""
    doi: str = ""

    authors: list[Author] = field(default_factory=list)
    affiliations: list[Affiliation] = field(default_factory=list)

    abstract: Abstract = field(default_factory=Abstract)
    keywords: Keywords = field(default_factory=Keywords)

    sections: list[Section] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    equations: list[Equation] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)

    funding: str = ""
    acknowledgements: str = ""
    conflict_of_interest: str = ""

    source_warnings: list[str] = field(default_factory=list)

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
                    "orcid": a.orcid,
                    "affiliations": a.affiliations,
                    "is_corresponding": a.is_corresponding,
                }
                for a in self.authors
            ],
            "affiliations": [
                {
                    "id": af.id,
                    "name": af.name,
                    "city": af.city,
                    "country": af.country,
                }
                for af in self.affiliations
            ],
            "abstract": {"ru": self.abstract.ru, "en": self.abstract.en},
            "keywords": {"ru": self.keywords.ru, "en": self.keywords.en},
            "sections": [
                {
                    "level": s.level,
                    "title": s.title,
                    "blocks": [
                        {"type": b.type, "text": b.text[:200] + "..." if len(b.text) > 200 else b.text}
                        for b in s.blocks
                    ],
                }
                for s in self.sections
            ],
            "figures": [
                {
                    "number": f.number,
                    "caption": f.caption,
                    "image_path": f.image_path,
                    "anchor_text": f.anchor_text,
                }
                for f in self.figures
            ],
            "tables": [
                {
                    "number": t.number,
                    "caption": t.caption,
                    "data": t.data,
                    "anchor_text": t.anchor_text,
                }
                for t in self.tables
            ],
            "equations": [
                {
                    "number": e.number,
                    "omml": e.omml,
                    "latex": e.latex,
                    "text": e.text,
                }
                for e in self.equations
            ],
            "references": [
                {
                    "number": r.number,
                    "raw_text": r.raw_text,
                    "doi": r.doi,
                    "url": r.url,
                }
                for r in self.references
            ],
            "funding": self.funding,
            "acknowledgements": self.acknowledgements,
            "conflict_of_interest": self.conflict_of_interest,
            "source_warnings": self.source_warnings,
        }