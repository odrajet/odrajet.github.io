#!/usr/bin/env python3
"""Build the ODRA JET landing v2 (ka / ru / en).

Head, CONFIG and the whole script come from frozen copies of the v1 pages in tools/v2/src/
(so the build is repeatable); layout comes from tools/v2/body.html + style.css, new strings
from tools/v2/i18n_add.json. Visible text is pre-rendered per language from I18N.

  python3 tools/build_v2.py          -> preview into v2/, v2/ru/, v2/en/ (noindex)
  python3 tools/build_v2.py --live   -> overwrite index.html, ru/index.html, en/index.html
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = ROOT / "tools" / "v2"
LIVE = "--live" in sys.argv
LANGS = ("ka", "ru", "en")
ADD = json.loads((T / "i18n_add.json").read_text(encoding="utf-8"))
CSS = (T / "style.css").read_text(encoding="utf-8")
BODY = (T / "body.html").read_text(encoding="utf-8")
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Georgian:wght@400;600;700;800'
         '&family=Noto+Sans:wght@400;600;700;800&family=Oswald:wght@500;600;700&display=swap">\n')

RENDER_ADD = '''    /* v2: every price, count and discount on the page is taken from CONFIG,
       so a price change or rollback in CONFIG cannot leave a stale badge behind. */
    const hasDiscount = showOldPrice && CONFIG.priceOld > CONFIG.priceRetail;
    const offPct = hasDiscount ? Math.round((CONFIG.priceOld - CONFIG.priceRetail) / CONFIG.priceOld * 100) : 0;
    document.querySelectorAll("[data-money]").forEach(el => { el.textContent = money(CONFIG[el.dataset.money]); });
    document.querySelectorAll("[data-num]").forEach(el => { el.textContent = String(CONFIG[el.dataset.num]); });
    document.querySelectorAll("[data-off]").forEach(el => { el.textContent = "\\u2212" + offPct + "%"; });
    document.querySelectorAll("[data-old]").forEach(el => { el.hidden = !hasDiscount; });
'''
RENDER_ANCHOR = '    document.getElementById("b2b-price").textContent = fill(t.b2bPrice);'

TUCK_OLD = """  (function tuckBar() {
    const bar = document.getElementById("mobile-bar");
    const anchor = document.querySelector(".hero .price-block");
    if (!bar || !anchor || !("IntersectionObserver" in window)) return;
    new IntersectionObserver(es => {
      bar.classList.toggle("tucked", es[0].isIntersecting);
    }, { threshold: 0.6 }).observe(anchor);
  })();"""
TUCK_NEW = """  /* v2: the bar also hides while either form is on screen — after a CTA jump it used to
     sit on top of the form's submit button and the consent line. */
  (function tuckBar() {
    const bar = document.getElementById("mobile-bar");
    const price = document.querySelector(".hero .price-block");
    if (!bar || !("IntersectionObserver" in window)) return;
    const on = new Set();
    const io = new IntersectionObserver(es => {
      es.forEach(e => {
        const hit = e.target === price ? e.intersectionRatio >= 0.6 : e.isIntersecting;
        if (hit) on.add(e.target); else on.delete(e.target);
      });
      bar.classList.toggle("tucked", on.size > 0);
    }, { threshold: [0, 0.6] });
    if (price) io.observe(price);
    document.querySelectorAll("form.lead-form").forEach(f => io.observe(f));
  })();"""


def parse_i18n(js):
    i = js.index("const I18N = {")
    j = js.index("\n};", i)
    parts = re.split(r"\n  (ka|ru|en): \{", js[i:j])
    out = {}
    for k in range(1, len(parts), 2):
        pairs = re.findall(r'^\s{4}(\w+):\s*"((?:[^"\\]|\\.)*)"', parts[k + 1], re.M)
        out[parts[k]] = {key: json.loads('"' + val + '"') for key, val in pairs}
    return out


def parse_config(js):
    def num(key):
        m = re.search(r"\b" + key + r":\s*(\d+)", js)
        return int(m.group(1)) if m else 0

    def txt(key):
        m = re.search(r"\b" + key + r':\s*"([^"]*)"', js)
        return m.group(1) if m else ""

    return {"priceRetail": num("priceRetail"), "priceOld": num("priceOld"),
            "priceWholesale": num("priceWholesale"), "pricePair": num("pricePair"), "wholesaleMin": num("wholesaleMin"),
            "deliveryTbilisi": num("deliveryTbilisi"), "brand": txt("brand"), "seller": txt("seller"),
            "id": txt("id"), "address": txt("address"), "email": txt("email")}


def build(lang):
    src = (T / "src" / (lang + ".html")).read_text(encoding="utf-8")
    sub = lang != "ka"                                   # ru/ and en/ sit one folder deeper
    R = ("../" if sub else "") if LIVE else ("../../" if sub else "../")
    priv = "privacy/" if LIVE else (R + (lang + "/" if sub else "") + "privacy/")
    links = {"ka": "../" if sub else "./", "ru": "../ru/" if sub else "ru/", "en": "../en/" if sub else "en/"}

    s0 = src.index("<script>\nconst IMAGES")
    js = src[s0:src.index("</script>", s0) + len("</script>")]
    I = parse_i18n(js)
    for L in LANGS:
        I[L].update(ADD[L])
    C = parse_config(js)
    t = I[lang]
    money = lambda n: f"{n} ₾"
    has_disc = bool(C["priceOld"]) and C["priceOld"] > C["priceRetail"]
    off = "−%d%%" % round((C["priceOld"] - C["priceRetail"]) / C["priceOld"] * 100) if has_disc else ""

    def fill(s):
        pairs = {"{delivery}": money(C["deliveryTbilisi"]) if C["deliveryTbilisi"] > 0 else t["deliveryFree"],
                 "{brand}": C["brand"], "{min}": str(C["wholesaleMin"]), "{price}": money(C["priceWholesale"]),
                 "{pair}": money(C["pricePair"]), "{pairTotal}": money(C["pricePair"] * 2),
                 "{seller}": C["seller"], "{id}": C["id"], "{address}": C["address"], "{email}": C["email"]}
        for k, v in pairs.items():
            s = s.replace(k, v)
        return s

    esc = lambda s: html.escape(s, quote=False)

    # ---- script: new strings, v2 image paths, CONFIG-driven prices
    hero = R + "img/v2_hero.jpg"
    js = re.sub(r"const IMAGES = \{.*?\};", "const IMAGES = " + json.dumps({L: {"hero": hero} for L in LANGS}) + ";", js, count=1)
    js = re.sub(r'videoUrl:\s*"[^"]*"', 'videoUrl: "' + R + 'video/odra.mp4"', js, count=1)
    js = re.sub(r'videoPoster:\s*"[^"]*"', 'videoPoster: "' + R + 'video/odra-poster.jpg"', js, count=1)
    for L in LANGS:
        lines = "".join("    %s: %s,\n" % (k, json.dumps(v, ensure_ascii=False)) for k, v in ADD[L].items())
        head = "\n  %s: {\n" % L
        assert js.count(head) == 1, (L, js.count(head))
        js = js.replace(head, head + lines, 1)
    assert js.count(RENDER_ANCHOR) == 1
    js = js.replace(RENDER_ANCHOR, RENDER_ADD + RENDER_ANCHOR, 1)
    assert js.count(TUCK_OLD) == 1
    js = js.replace(TUCK_OLD, TUCK_NEW, 1)

    # ---- head: v1 head with light colour scheme, noindex for the preview, new description
    head = src[: src.index("</head>")]
    head = re.sub(r'<meta name="theme-color" content="[^"]*">', '<meta name="theme-color" content="#111111">', head)
    head = head.replace('initial-scale=1,viewport-fit=cover">', 'initial-scale=1,viewport-fit=cover">\n<meta name="color-scheme" content="light">', 1)
    if not LIVE:
        head = head.replace('<meta name="color-scheme" content="light">', '<meta name="color-scheme" content="light">\n<meta name="robots" content="noindex, nofollow">', 1)
    head = re.sub(r'<link rel="icon" href="[^"]*"', '<link rel="icon" href="' + R + 'favicon.svg"', head)
    d = html.escape(t["metaDesc"], quote=True)
    head = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + d, head)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + d, head)
    head = re.sub(r'(<meta name="twitter:description" content=")[^"]*', lambda m: m.group(1) + d, head)

    # ---- body: placeholders, then pre-render every data-i18n / price node
    b = BODY
    rep = {"R": R, "PRIV": priv, "L_KA": links["ka"], "L_RU": links["ru"], "L_EN": links["en"],
           "P_KA": str(lang == "ka").lower(), "P_RU": str(lang == "ru").lower(), "P_EN": str(lang == "en").lower(),
           "BRAND": esc(C["brand"]), "OLD": money(C["priceOld"]), "RETAIL": money(C["priceRetail"]),
           "WHOLESALE": money(C["priceWholesale"]), "MIN": str(C["wholesaleMin"]), "OFF": off, "HERO": hero,
           "PH_NAME": esc(t["fName"]), "PH_PHONE": esc(t["fPhone"]),
           "B2BPRICE": esc(fill(t["b2bPrice"])), "FOOTER": esc(fill(t["footer"])), "LEGAL": esc(fill(t["legalLine"]))}
    for k, v in rep.items():
        b = b.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{\w+\}\}", b)
    assert not left, left
    missing = []

    def i18n_node(m):
        key = m.group("key")
        if key not in t:
            missing.append(key)
            return m.group(0)
        return m.group("open") + esc(fill(t[key])) + "</" + m.group("tag") + ">"

    b = re.sub(r'(?P<open><(?P<tag>[a-z0-9]+)\b[^>]*\bdata-i18n="(?P<key>\w+)"[^>]*>)</(?P=tag)>', i18n_node, b)
    b = re.sub(r'<img\b[^>]*\bdata-i18n-alt="(\w+)"[^>]*>',
               lambda m: m.group(0).replace('alt=""', 'alt="' + html.escape(fill(t[m.group(1)]), quote=True) + '"'), b)
    b = re.sub(r'(<(?P<tag>\w+)\b[^>]*\bdata-money="(?P<k>\w+)"[^>]*>)[^<]*(</(?P=tag)>)',
               lambda m: m.group(1) + money(C[m.group("k")]) + m.group(4), b)
    b = re.sub(r'(<(?P<tag>\w+)\b[^>]*\bdata-num="(?P<k>\w+)"[^>]*>)[^<]*(</(?P=tag)>)',
               lambda m: m.group(1) + str(C[m.group("k")]) + m.group(4), b)
    if not has_disc:
        b = re.sub(r"<(\w+)([^>]*\bdata-old\b[^>]*)>", r"<\1\2 hidden>", b)
    assert not missing, missing
    empty = re.findall(r'<([a-z0-9]+)\b[^>]*\bdata-i18n="(\w+)"[^>]*></\1>', b)
    assert not empty, empty

    page = (head + "</head>\n<body>\n\n" + FONTS + "\n<style>\n" + CSS + "</style>\n\n" + b + "\n\n" + js + "\n</body>\n</html>\n")
    out = (ROOT if LIVE else ROOT / "v2") / ("" if lang == "ka" else lang) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out, len(page)


if __name__ == "__main__":
    for L in LANGS:
        p, n = build(L)
        print(p.relative_to(ROOT), n)
