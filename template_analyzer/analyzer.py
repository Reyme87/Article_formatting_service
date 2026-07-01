from docx import Document

TEMPLATE_STYLE_MAP = {
    "MDPI_1.2_title": "title",
    "MDPI_1.3_authornames": "authors_line",
    "MDPI_1.6_affiliation": "affiliation",
    "MDPI_1.7_abstract": "abstract",
    "MDPI_1.8_keywords": "keywords",
    "MDPI_2.1_heading1": "section_heading",
    "MDPI_3.1_text": "section_text",
    "MDPI_5.1_figure_caption": "figure_caption",
    "MDPI_8.1_references": "reference_item",
}


def inspect_template(docx_path: str) -> list[dict]:
    doc = Document(docx_path)
    result = []
    for i, para in enumerate(doc.paragraphs):
        style_name = para.style.name if para.style else "Normal"
        result.append({
            "index": i,
            "style": style_name,
            "text": para.text.strip(),
            "mapped_field": TEMPLATE_STYLE_MAP.get(style_name, None),
        })
    return result


def print_template_structure(docx_path: str):
    items = inspect_template(docx_path)
    print(f"Всего абзацев в шаблоне: {len(items)}\n")
    for item in items:
        marker = f"  <- {item['mapped_field']}" if item["mapped_field"] else ""
        text_preview = item["text"][:70] if item["text"] else "(пусто)"
        print(f"[{item['index']:3}] {item['style']:28} {text_preview}{marker}")