#!/usr/bin/env python3
"""Собирает страницы «Спасибо» после отправленного заказа: /spasibo/, /ru/spasibo/, /en/spasibo/.

Форма заказа (v3/index.html) после успешной отправки переводит сюда с ?id=&n=&v=.
Здесь пиксель шлёт Purchase (цель холодных кампаний) — один раз на заказ (id запоминается в браузере).
Запуск из корня репозитория: python3 tools/build_spasibo.py
"""
import json
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIXEL = "1047116104717565"
WA = "995599703991"
T = {
    "ka": {
        "title": "მადლობა! შეკვეთა მიღებულია",
        "text": "მალე მოგწერთ WhatsApp-ში ნომრიდან +995 599 703 991, რომ დავადასტუროთ შეკვეთა და მიტანა. არ გინდათ ლოდინი? მოგვწერეთ თავად.",
        "sum": "{n} ც. · {v} ₾ მიტანის ჩათვლით · გადახდა კურიერთან, ნაღდი ფულით",
        "wa": "მოგვწერეთ WhatsApp-ში",
        "waText": "გამარჯობა! საიტზე შევუკვეთე დასაკეცი საწოლი.",
        "back": "საიტზე დაბრუნება",
        "home": "../",
    },
    "ru": {
        "title": "Спасибо! Заказ принят",
        "text": "Скоро напишем вам в WhatsApp с номера +995 599 703 991, чтобы подтвердить заказ и доставку. Не хотите ждать? Напишите нам сами.",
        "sum": "{n} шт. · {v} ₾ с доставкой · оплата курьеру наличными",
        "wa": "Написать в WhatsApp",
        "waText": "Здравствуйте! Я оформил(а) заказ раскладушки на сайте.",
        "back": "Вернуться на сайт",
        "home": "../",
    },
    "en": {
        "title": "Thank you! Order received",
        "text": "We will message you on WhatsApp from +995 599 703 991 soon to confirm the order and delivery. Don't want to wait? Message us yourself.",
        "sum": "{n} pcs · {v} ₾ incl. delivery · cash to the courier",
        "wa": "Message us on WhatsApp",
        "waText": "Hello! I placed an order for the folding bed on the website.",
        "back": "Back to the website",
        "home": "../",
    },
}
OUT = {"ka": "spasibo/index.html", "ru": "ru/spasibo/index.html", "en": "en/spasibo/index.html"}

TPL = """<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ODRA JET — __TITLE__</title>
<meta name="robots" content="noindex">
<link rel="icon" href="__UP__favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Georgian:wght@400;600;800&family=Inter:wght@400;600;800&display=swap">
<style>
  :root { color-scheme: light; --bg: #f6f3ef; --card: #fff; --ink: #161616; --muted: #6b6661; --line: #e6e0d9; --ok: #1f8a4c; --wa: #25d366; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px 16px; background: var(--bg); color: var(--ink);
         font-family: "Inter", system-ui, sans-serif; line-height: 1.5; }
  :root[lang="ka"] body { font-family: "Noto Sans Georgian", "Inter", system-ui, sans-serif; }
  .card { width: 100%; max-width: 460px; background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 32px 24px; text-align: center; }
  .ok { width: 64px; height: 64px; margin: 0 auto 16px; border-radius: 50%; background: var(--ok); color: #fff; display: grid; place-items: center; font-size: 34px; font-weight: 800; }
  h1 { font-size: 26px; line-height: 1.2; margin: 0 0 12px; }
  p { margin: 0 0 16px; color: var(--muted); }
  .sum { color: var(--ink); font-weight: 600; background: var(--bg); border-radius: 10px; padding: 10px 12px; }
  .btn { display: block; padding: 15px 18px; border-radius: 12px; font-weight: 800; text-decoration: none; margin-top: 8px; }
  .btn-wa { background: var(--wa); color: #fff; }
  .back { display: inline-block; margin-top: 16px; color: var(--muted); font-size: 14px; }
</style>
</head>
<body>
<main class="card">
  <div class="ok" aria-hidden="true">✓</div>
  <h1>__TITLE__</h1>
  <p>__TEXT__</p>
  <p class="sum" id="sum" hidden></p>
  <a class="btn btn-wa" href="https://wa.me/__WA__?text=__WATEXT__" target="_blank" rel="noopener">__WABTN__</a>
  <a class="back" href="__HOME__">__BACK__</a>
</main>
<script>
(function () {
  const q = new URLSearchParams(location.search);
  const id = (q.get("id") || "").slice(0, 40), n = parseInt(q.get("n"), 10), v = parseFloat(q.get("v"));
  const ok = id && n > 0 && n < 100 && v > 0 && v < 100000;
  if (ok) { const el = document.getElementById("sum"); el.textContent = __SUM__.replace("{n}", n).replace("{v}", v); el.hidden = false; }

  /* пиксель Meta: как на сайте — работает, если человек не нажал «Отказаться» */
  let c = null; try { c = localStorage.getItem("odra.consent.ads"); } catch (e) {}
  if (c === "no") return;
  !function (f, b, e, u, n, t, s) {
    if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments) };
    if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = "2.0"; n.queue = [];
    t = b.createElement(e); t.async = !0; t.src = u; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s)
  }(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");
  fbq("init", "__PIXEL__");
  fbq("track", "PageView");
  /* Purchase — только для настоящего заказа (есть id) и один раз: обновление страницы не считается */
  if (!ok) return;
  const key = "odra.purchase." + id;
  let seen = null; try { seen = localStorage.getItem(key); } catch (e) {}
  if (seen) return;
  try { localStorage.setItem(key, "1"); } catch (e) {}
  fbq("track", "Purchase", {
    value: v, currency: "GEL", num_items: n, content_name: "odra-jet-folding-bed",
    lang: "__LANG__", source: q.get("src") || "direct", campaign: q.get("c") || "none"
  }, { eventID: "order-" + id });
})();
</script>
</body>
</html>
"""

for lang, out in OUT.items():
    t = T[lang]
    up = "../" if lang == "ka" else "../../"
    s = TPL
    for k, val in {
        "__LANG__": lang, "__TITLE__": t["title"], "__TEXT__": t["text"], "__UP__": up,
        "__WA__": WA, "__WATEXT__": quote(t["waText"]), "__WABTN__": t["wa"],
        "__HOME__": t["home"], "__BACK__": t["back"], "__SUM__": json.dumps(t["sum"], ensure_ascii=False),
        "__PIXEL__": PIXEL,
    }.items():
        s = s.replace(k, val)
    p = ROOT / out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")
    print("собрано:", out)
