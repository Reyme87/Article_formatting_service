import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from article_extractor.extractor import extract_article
from template_analyzer.dot_fixer import fix_dot_to_docx
from template_analyzer.analyzer import print_template_structure

ARTICLE_PATH = "samples/articles/Волков статья.docx"
TEMPLATE_DOT_PATH = "samples/templates/technologies-template(1).dot"
TEMPLATE_FIXED_PATH = "output/technologies-template_fixed.docx"

def main():
    print("=" * 60)
    print("Шаг 1: Извлечение данных из статьи")
    print("=" * 60)

    article = extract_article(ARTICLE_PATH)

    print(f"\n📌 Название (RU): {article.title_ru or '❌ не найдено'}")
    print(f"📌 Название (EN): {article.title_en or '⚠️  отсутствует'}")
    print(f"📌 УДК: {article.udc or '—'}")
    print(f"📌 DOI: {article.doi or '—'}")

    print(f"\n👤 Авторы ({len(article.authors)}):")
    for a in article.authors:
        affil_ids = ", ".join(str(x) for x in a.affiliations)
        print(f"   • {a.initials_name}  |  {a.email}  |  affiliations: [{affil_ids}]")

    print(f"\n📝 Аннотация (RU, первые 200 симв.):")
    print(f"   {article.abstract.ru[:200]}..." if article.abstract.ru else "   ❌ не найдена")

    print(f"\n🔑 Ключевые слова (RU):")
    for kw in article.keywords.ru:
        print(f"   • {kw}")

    print(f"\n📚 Разделы ({len(article.sections)}):")
    for s in article.sections:
        print(f"   [{s.level}] {s.title}  ({len(s.blocks)} блоков)")

    print(f"\n🖼  Рисунки ({len(article.figures)}):")
    for f in article.figures:
        print(f"   • Рис. {f.number}: {f.caption[:80]}")

    print(f"\n📖 Литература ({len(article.references)} источников)")
    if article.references:
        print(f"   Первый: {article.references[0].raw_text[:80]}...")

    print(f"\n💰 Финансирование: {'да' if article.funding else 'нет'}")

    print(f"\n⚠️  Предупреждения ({len(article.source_warnings)}):")
    for w in article.source_warnings:
        print(f"   ⚠️  {w}")

    os.makedirs("output", exist_ok=True)
    out_path = "output/article_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(article.to_dict(), f, ensure_ascii=False, indent=2)

    print(f"\n✅ Данные сохранены в {out_path}")

    # ============================================================
    print("\n" + "=" * 60)
    print("Шаг 2: Анализ шаблона")
    print("=" * 60)

    print(f"\n🔧 Чиним .dot файл -> .docx ...")
    fixed_path = fix_dot_to_docx(TEMPLATE_DOT_PATH, TEMPLATE_FIXED_PATH)
    print(f"✅ Исправленный файл сохранён: {fixed_path}")

    print(f"\n📋 Структура шаблона:\n")
    print_template_structure(fixed_path)


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    main()