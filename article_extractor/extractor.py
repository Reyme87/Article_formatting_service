import re
from docx import Document

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.schemas import (
    ArticleData, Author, Affiliation,
    Section, Block, Figure, Reference
)

KNOWN_SECTION_HEADERS = {
    "введение", "introduction", "архитектура", "алгоритм",
    "интеграция", "программная реализация", "заключение",
    "conclusion", "материалы и методы", "materials and methods",
    "результаты", "results", "обсуждение", "discussion",
}

HEADING_STYLES = {
    "heading 1", "heading 2", "heading 3",
    "заголовок 1", "заголовок 2", "заголовок 3"
}


def _text(para) -> str:
    return para.text.strip()


def _is_bold(para) -> bool:
    runs = [r for r in para.runs if r.text.strip()]
    if not runs:
        return False
    return all(r.bold for r in runs)


def _is_italic(para) -> bool:
    runs = [r for r in para.runs if r.text.strip()]
    if not runs:
        return False
    return all(r.italic for r in runs)


def _is_heading_style(para) -> bool:
    style = para.style.name.lower() if para.style else ""
    return style in HEADING_STYLES or style.startswith("heading")


def _looks_like_section_header(text: str) -> bool:
    if not text or len(text) > 120:
        return False
    lower = text.lower().strip()
    for kw in KNOWN_SECTION_HEADERS:
        if lower.startswith(kw):
            return True
    return bool(re.match(r"^\d+[\.\s]", text))


def extract_article(docx_path: str) -> ArticleData:
    doc = Document(docx_path)
    data = ArticleData()
    paragraphs = doc.paragraphs

    i = 0
    current_section: Section | None = None
    found_abstract = False
    in_references = False

    while i < len(paragraphs):
        para = paragraphs[i]
        t = _text(para)
        if not t:
            i += 1
            continue
        lower = t.lower()

        # --- УДК / DOI ---
        if "удк" in lower:
            m = re.search(r"УДК\s*([\d.]+)", t, re.IGNORECASE)
            if m:
                data.udc = m.group(1)
            m = re.search(r"DOI\s*[:\s]*([\S]+)", t, re.IGNORECASE)
            if m:
                raw = m.group(1).strip(":")
                if raw:
                    data.doi = raw
            i += 1
            continue

        # --- Название ---
        if not data.title_ru and _is_bold(para) and len(t) > 20 and not found_abstract:
            if not re.match(r"^[А-ЯA-Z][а-яa-z]+\s+[А-ЯA-Z]\.", t):
                data.title_ru = t
                i += 1
                continue

        # --- Авторы ---
        if not found_abstract and _is_bold(para):
            m = re.match(r"^([А-ЯA-Z]\.\s*[А-ЯA-Z]\.\s+[А-ЯA-Zа-яa-z\-]+)$", t)
            if m:
                data.authors.append(Author(initials_name=m.group(1)))
                i += 1
                continue

        # --- Email ---
        if re.match(r"^[\w\.\-]+@[\w\.\-]+\.\w+$", t):
            if data.authors:
                data.authors[-1].email = t
            i += 1
            continue

        # --- Аффилиация (курсив) ---
        if not found_abstract and _is_italic(para):
            if data.authors:
                lines = [t]
                j = i + 1
                while j < len(paragraphs):
                    nt = _text(paragraphs[j])
                    if not nt or not _is_italic(paragraphs[j]):
                        break
                    lines.append(nt)
                    j += 1

                raw_affil = " | ".join(lines)
                city, country = "", ""
                city_match = re.search(r"г\.\s*([А-Яа-я\-]+)", raw_affil)
                if city_match:
                    city = city_match.group(1)
                if "Россия" in raw_affil or "Russia" in raw_affil:
                    country = "Россия"

                affil_id = len(data.affiliations) + 1
                data.affiliations.append(Affiliation(
                    id=affil_id,
                    name=lines[0],
                    city=city,
                    country=country,
                ))
                if data.authors and not data.authors[-1].affiliations:
                    data.authors[-1].affiliations = [affil_id]

                i = j
                continue

        # --- Ключевые слова ---
        if "ключевые слова" in lower or "keywords" in lower:
            kw_text = re.sub(r"ключевые слова\s*[:：]?\s*", "", t, flags=re.IGNORECASE)
            kw_text = re.sub(r"keywords\s*[:：]?\s*", "", kw_text, flags=re.IGNORECASE)
            sep = ";" if ";" in kw_text else ","
            data.keywords.ru = [k.strip().rstrip(".") for k in kw_text.split(sep) if k.strip()]
            i += 1
            continue

        # --- Аннотация ---
        if "аннотация" in lower or ("abstract" in lower and not found_abstract):
            found_abstract = True
            body = re.sub(r"аннотация\s*[:：]?\s*", "", t, flags=re.IGNORECASE)
            body = re.sub(r"abstract\s*[:：]?\s*", "", body, flags=re.IGNORECASE)
            if len(body) > 30:
                data.abstract.ru = body.strip()
            else:
                i += 1
                parts = []
                while i < len(paragraphs):
                    nt = _text(paragraphs[i])
                    if not nt or "ключевые слова" in nt.lower():
                        break
                    parts.append(nt)
                    i += 1
                data.abstract.ru = " ".join(parts).strip()
            i += 1
            continue

        # --- Список литературы ---
        if re.match(r"^(список литературы|references)\s*$", lower):
            in_references = True
            i += 1
            continue

        if in_references:
            doi, url = "", ""
            doi_m = re.search(r"DOI\s+([\S]+)", t, re.IGNORECASE)
            if doi_m:
                doi = doi_m.group(1).strip(".")
            url_m = re.search(r"https?://[\S]+", t)
            if url_m:
                url = url_m.group(0).strip(".")
            data.references.append(Reference(
                number=len(data.references) + 1,
                raw_text=t,
                doi=doi,
                url=url,
            ))
            i += 1
            continue

        # --- Финансирование ---
        if "финансов" in lower or "при поддержке" in lower or "funding" in lower:
            data.funding = t
            i += 1
            continue

        # --- Рисунки ---
        fig_m = re.match(r"^рисун[оке]{1,2}\s+(\d+)[\.!\s](.*)$", lower)
        if fig_m:
            fig_num = int(fig_m.group(1))
            data.figures.append(Figure(
                number=fig_num,
                caption=t,
                anchor_text=f"Рисунок {fig_num}",
            ))
            i += 1
            continue

        # --- Заголовки разделов ---
        is_section = _is_heading_style(para) or (
            _is_bold(para) and _looks_like_section_header(t) and found_abstract
        )
        if is_section and not in_references:
            current_section = Section(level=1, title=t, blocks=[])
            data.sections.append(current_section)
            i += 1
            continue

        # --- Обычный текст → Block ---
        if current_section is not None and found_abstract and not in_references:
            current_section.blocks.append(Block(type="paragraph", text=t))

        i += 1

    _postprocess(data)
    return data


def _postprocess(data: ArticleData):
    if not data.title_ru:
        data.source_warnings.append("Не найдено название статьи")
    if not data.authors:
        data.source_warnings.append("Не найдены авторы")
    if not data.abstract.ru:
        data.source_warnings.append("Не найдена аннотация")
    if not data.abstract.en:
        data.source_warnings.append("Отсутствует английская аннотация (нужна для шаблона)")
    if not data.keywords.ru:
        data.source_warnings.append("Не найдены ключевые слова")
    if not data.keywords.en:
        data.source_warnings.append("Отсутствуют английские ключевые слова (нужны для шаблона)")
    if not data.sections:
        data.source_warnings.append("Не найдены разделы статьи")
    if not data.references:
        data.source_warnings.append("Не найден список литературы")
    if not data.title_en:
        data.source_warnings.append("Отсутствует английское название (нужно для шаблона)")