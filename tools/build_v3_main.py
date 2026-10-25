#!/usr/bin/env python3
"""Собирает главные страницы сайта (/, /ru/, /en/) из предпросмотра v3/index.html.

Картинки и ролики остаются в v3/ (form/, reviews/), страницы ссылаются на них.
SEO-теги (description, canonical, hreflang, og, twitter) берутся из tools/v3_main/head_<lang>.html.
Запуск из корня репозитория: python3 tools/build_v3_main.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = (ROOT / "v3" / "index.html").read_text(encoding="utf-8")
TITLES = {
    "ka": "ODRA JET — დასაკეცი საწოლი მატრასით · თბილისი",
    "ru": "ODRA JET — раскладушка с матрасом · Тбилиси",
    "en": "ODRA JET — folding bed with mattress · Tbilisi",
}
PAGES = [("ka", "index.html", ""), ("ru", "ru/index.html", "../"), ("en", "en/index.html", "../")]


def rep(s, a, b, must=True):
    if must and a not in s:
        raise SystemExit(f"не найдено в v3/index.html: {a!r}")
    return s.replace(a, b)


for lang, out, up in PAGES:
    s = SRC
    head = (ROOT / "tools" / "v3_main" / f"head_{lang}.html").read_text(encoding="utf-8")
    s = rep(s, '<html lang="ka">', f'<html lang="{lang}">')
    s = rep(s, "<title>ODRA JET — დასაკეცი საწოლი მატრასით</title>", f"<title>{TITLES[lang]}</title>")
    s = rep(s, '<meta name="robots" content="noindex">\n',
            head + f'<script>window.__FORCE_LANG__ = "{lang}"; window.__PAGE__ = "main-{lang}";</script>\n')
    # пути: ресурсы v3 и общие файлы сайта
    v3 = up + "v3/"
    for a in ['src="form/', 'data-src-lang="form/', '"reviews/']:
        s = rep(s, a, a.replace("form/", v3 + "form/").replace('"reviews/', '"' + v3 + "reviews/"))
    s = rep(s, '"../video/', '"' + up + "video/")
    s = rep(s, 'href="../favicon.svg"', f'href="{up}favicon.svg"')
    s = rep(s, 'href="../privacy/"', 'href="privacy/"')
    # язык страницы важнее сохранённого в браузере (параметр ?lang= всё ещё главнее)
    s = rep(s, "    if (I18N[q]) return q;\n", "    if (I18N[q]) return q;\n    if (I18N[window.__FORCE_LANG__]) return window.__FORCE_LANG__;\n")
    (ROOT / out).write_text(s, encoding="utf-8")
    print("собрано:", out)
