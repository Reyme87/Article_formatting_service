import re
from docx import Document
from docx.oxml.ns import qn

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.schemas import ArticleData, Author, Abstract, Keywords, Section, Figure, Reference


# Заголовки разделов, которые мы умеем распознавать
KNOWN_SECTION_HEADERS = {
    "введение": 1,
    "introduction": 1,
    "архитектура": 1,
    "алгоритм": 1,
    "интеграция": 1,
    "программная реализация": 1,
    "заключение": 1,
    "conclusion": 1,
    "материалы и методы": 1,
    "materials and methods": 1,
    "результаты": 1,
    "results": 1,
    "обсуждение": 1,
    "discussion": 1,
}

# Стили Word, которые считаются заголовками
HEADING_STYLES = {"heading 1", "heading 2", "heading 3", "заголовок 1", "заголовок 2", "заголовок 3"}


def _get_paragraph_text(para) -> str:
    return para.text.strip()


def _is_bold(para) -> bool:
    runs = [r for r in para.runs if r.text.strip()]
    if not runs:
        return False
    return all(r.bold for r in runs)


def _is_heading_style(para) -> bool:
    style_name = para.style.name.lower() if para.style else ""
    return style_name in HEADING_STYLES or style_name.startswith("heading")


def _looks_like_section_header(text: str) -> bool:
    if not text:
        return False
    if len(text) > 120:
        return False
    lower = text.lower().strip()
    for kw in KNOWN_SECTION_HEADERS:
        if lower.startswith(kw):
            return True
    if re.match(r"^\d+[\.\s]", text):
        return True
    return False


def extract_article(docx_path: str) -> ArticleData:
    doc = Document(docx_path)
    data = ArticleData()

    paragraphs = doc.paragraphs

    i = 0
    current_section: Section | None = None
    found_abstract = False
    found_keywords = False
    found_references = False
    in_references = False

    header_block = []

    while i < len(paragraphs):
        para = paragraphs[i]
        text = _get_paragraph_text(para)

        if not text:
            i += 1
            continue

        lower = text.lower()

        # --- УДК / DOI ---
        if "удк" in lower or "udk" in lower:
            udc_match = re.search(r"УДК\s*([\d.]+)", text, re.IGNORECASE)
            doi_match = re.search(r"DOI\s*[:\s]*([\S]+)", text, re.IGNORECASE)
            if udc_match:
                data.udc = udc_match.group(1)
            if doi_match:
                raw_doi = doi_match.group(1).strip(":").strip()
                if raw_doi:
                    data.doi = raw_doi
            i += 1
            continue

        # --- Название статьи ---
        if not data.title_ru and _is_bold(para) and len(text) > 20 and not found_abstract:
            if not re.match(r"^[А-ЯA-Z][а-яa-z]+\s+[А-ЯA-Z]\.", text):
                data.title_ru = text
                i += 1
                continue

        # --- Авторы ---
        if not found_abstract and _is_bold(para):
            author_match = re.match(r"^([А-ЯA-Z]\.\s*[А-ЯA-Z]\.\s+[А-ЯA-Zа-яa-z\-]+)$", text)
            if author_match:
                author = Author()
                author.initials_name = author_match.group(1)
                data.authors.append(author)
                i += 1
                continue

        # --- Email ---
        if re.match(r"^[\w\.\-]+@[\w\.\-]+\.\w+$", text):
            if data.authors:
                data.authors[-1].email = text
            i += 1
            continue

        # --- Организация / аффилиация (курсив) ---
        if not found_abstract and para.runs and all(r.italic for r in para.runs if r.text.strip()):
            if data.authors and not data.authors[-1].affiliation:
                affil_lines = [text]
                j = i + 1
                while j < len(paragraphs):
                    next_text = _get_paragraph_text(paragraphs[j])
                    if not next_text:
                        break
                    next_runs = [r for r in paragraphs[j].runs if r.text.strip()]
                    if next_runs and all(r.italic for r in next_runs):
                        affil_lines.append(next_text)
                        j += 1
                    else:
                        break
                data.authors[-1].affiliation = " | ".join(affil_lines)
                i = j
                continue

        # --- Ключевые слова ---
        if "ключевые слова" in lower or "keywords" in lower:
            found_keywords = True
            kw_text = re.sub(r"ключевые слова\s*[:：]?\s*", "", text, flags=re.IGNORECASE)
            kw_text = re.sub(r"keywords\s*[:：]?\s*", "", kw_text, flags=re.IGNORECASE)
            if ";" in kw_text:
                kws = [k.strip().rstrip(".") for k in kw_text.split(";") if k.strip()]
            else:
                kws = [k.strip().rstrip(".") for k in kw_text.split(",") if k.strip()]
            data.keywords.ru = kws
            i += 1
            continue

        # --- Аннотация ---
        if "аннотация" in lower or "abstract" in lower:
            found_abstract = True
            abstract_text = re.sub(r"аннотация\s*[:：]?\s*", "", text, flags=re.IGNORECASE)
            abstract_text = re.sub(r"abstract\s*[:：]?\s*", "", abstract_text, flags=re.IGNORECASE)

            if len(abstract_text) > 30:
                data.abstract.ru = abstract_text.strip()
            else:
                i += 1
                while i < len(paragraphs):
                    next_text = _get_paragraph_text(paragraphs[i])
                    if not next_text:
                        break
                    if "ключевые слова" in next_text.lower():
                        break
                    data.abstract.ru += " " + next_text
                    i += 1
                data.abstract.ru = data.abstract.ru.strip()
            i += 1
            continue

        # --- Список литературы ---
        if re.match(r"^(список литературы|references)\s*$", lower):
            in_references = True
            found_references = True
            i += 1
            continue

        if in_references:
            ref_num = len(data.references) + 1
            data.references.append(Reference(number=ref_num, raw_text=text))
            i += 1
            continue

        # --- Финансирование ---
        if "финансов" in lower or "при поддержке" in lower or "funding" in lower:
            data.funding = text
            i += 1
            continue

        # --- Рисунки (подписи) ---
        fig_match = re.match(r"^рисун[оке]{1,2}\s+(\d+)[\.!\s](.*)$", lower)
        if fig_match:
            fig_num = int(fig_match.group(1))
            caption = text
            data.figures.append(Figure(number=fig_num, caption=caption))
            i += 1
            continue

        # --- Разделы ---
        is_section = _is_heading_style(para) or (
            _is_bold(para) and _looks_like_section_header(text) and found_abstract
        )
        if is_section and not in_references:
            current_section = Section(level=1, title=text, text="")
            data.sections.append(current_section)
            i += 1
            continue

        # --- Обычный текст ---
        if current_section is not None and found_abstract and not in_references:
            if current_section.text:
                current_section.text += "\n" + text
            else:
                current_section.text = text

        i += 1

    _postprocess(data)
    return data


def _postprocess(data: ArticleData):
    if not data.title_ru:
        data.warnings.append("Не найдено название статьи")
    if not data.authors:
        data.warnings.append("Не найдены авторы")
    if not data.abstract.ru:
        data.warnings.append("Не найдена аннотация")
    if not data.abstract.en:
        data.warnings.append("Отсутствует английская аннотация (нужна для шаблона)")
    if not data.keywords.ru:
        data.warnings.append("Не найдены ключевые слова")
    if not data.keywords.en:
        data.warnings.append("Отсутствуют английские ключевые слова (нужны для шаблона)")
    if not data.sections:
        data.warnings.append("Не найдены разделы статьи")
    if not data.references:
        data.warnings.append("Не найден список литературы")
    if not data.title_en:
        data.warnings.append("Отсутствует английское название (нужно для шаблона)")