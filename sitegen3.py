#!/usr/bin/env python3
"""RateNow v2 - self-updating currency site generator (static, free hosting, zero runtime AI tokens).
  python sitegen2.py            live rates + real history bootstrap
  python sitegen2.py --sample   offline test (synthetic history, NEVER use for the live site)
"""
import json, os, sys, shutil, datetime, random, struct, zlib, math, urllib.request
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
DATA = os.path.join(ROOT, "data")
ASSETS = os.path.join(ROOT, "assets")
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
SITE = CFG["site_url"].rstrip("/")
NAME = CFG["site_name"]
TODAY = datetime.date.today().isoformat()
SAMPLE_MODE = "--sample" in sys.argv

CUR = {
 "USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound", "PKR": "Pakistani Rupee",
 "INR": "Indian Rupee", "AED": "UAE Dirham", "SAR": "Saudi Riyal", "CAD": "Canadian Dollar",
 "AUD": "Australian Dollar", "CNY": "Chinese Yuan", "JPY": "Japanese Yen", "CHF": "Swiss Franc",
 "TRY": "Turkish Lira", "SGD": "Singapore Dollar", "MYR": "Malaysian Ringgit", "BDT": "Bangladeshi Taka",
 "NZD": "New Zealand Dollar", "ZAR": "South African Rand", "SEK": "Swedish Krona", "NOK": "Norwegian Krone",
 "DKK": "Danish Krone", "HKD": "Hong Kong Dollar", "KRW": "South Korean Won", "THB": "Thai Baht",
 "IDR": "Indonesian Rupiah", "PHP": "Philippine Peso", "EGP": "Egyptian Pound", "QAR": "Qatari Riyal",
 "KWD": "Kuwaiti Dinar", "BHD": "Bahraini Dinar", "OMR": "Omani Rial", "NGN": "Nigerian Naira",
 "KES": "Kenyan Shilling", "BRL": "Brazilian Real", "MXN": "Mexican Peso", "PLN": "Polish Zloty",
 "XAU": "Gold (1 troy oz)", "XAG": "Silver (1 troy oz)",
}
UR = {
 "USD": "امریکی ڈالر", "EUR": "یورو", "GBP": "برطانوی پاؤنڈ", "PKR": "پاکستانی روپیہ", "INR": "بھارتی روپیہ",
 "AED": "یو اے ای درہم", "SAR": "سعودی ریال", "CAD": "کینیڈین ڈالر", "AUD": "آسٹریلین ڈالر", "CNY": "چینی یوآن",
 "JPY": "جاپانی ین", "CHF": "سوئس فرانک", "TRY": "ترک لیرا", "SGD": "سنگاپور ڈالر", "MYR": "ملائیشین رنگٹ",
 "BDT": "بنگلہ دیشی ٹکا", "NZD": "نیوزی لینڈ ڈالر", "ZAR": "جنوبی افریقی رینڈ", "SEK": "سویڈش کرونا",
 "NOK": "نارویجن کرونر", "DKK": "ڈینش کرونر", "HKD": "ہانگ کانگ ڈالر", "KRW": "جنوبی کوریائی وون",
 "THB": "تھائی باہت", "IDR": "انڈونیشین روپیہ", "PHP": "فلپائنی پیسو", "EGP": "مصری پاؤنڈ", "QAR": "قطری ریال",
 "KWD": "کویتی دینار", "BHD": "بحرینی دینار", "OMR": "عمانی ریال", "NGN": "نائجیرین نائرا", "KES": "کینیائی شلنگ",
 "BRL": "برازیلین ریئل", "MXN": "میکسیکن پیسو", "PLN": "پولش زلوٹی", "XAU": "سونا (ایک اونس)", "XAG": "چاندی (ایک اونس)",
}
METALS = {"XAU", "XAG"}
SAMPLE = {"USD":1,"EUR":0.92,"GBP":0.79,"PKR":280,"INR":83.2,"AED":3.6725,"SAR":3.75,"CAD":1.36,"AUD":1.52,
 "CNY":7.24,"JPY":149.5,"CHF":0.88,"TRY":28.5,"SGD":1.35,"MYR":4.7,"BDT":110,"NZD":1.65,"ZAR":18.8,"SEK":10.9,
 "NOK":10.8,"DKK":6.9,"HKD":7.82,"KRW":1350,"THB":36,"IDR":15800,"PHP":56,"EGP":30.9,"QAR":3.64,"KWD":0.31,
 "BHD":0.376,"OMR":0.385,"NGN":770,"KES":150,"BRL":5.0,"MXN":17.8,"PLN":4.1,"XAU":0.000375,"XAG":0.0344}
POPULAR = [("USD","PKR"),("USD","INR"),("EUR","USD"),("GBP","USD"),("USD","AED"),("USD","SAR"),("USD","CAD"),
 ("AUD","USD"),("EUR","PKR"),("GBP","PKR"),("AED","PKR"),("SAR","PKR"),("USD","BDT"),("USD","EGP"),("USD","TRY"),
 ("EUR","GBP"),("USD","JPY"),("USD","CNY"),("GBP","INR"),("AED","INR"),("CAD","PKR"),("AUD","PKR"),
 ("QAR","PKR"),("KWD","PKR"),("OMR","PKR"),("MYR","PKR"),("CNY","PKR"),("INR","PKR")]
AMOUNTS = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000]
AMT2 = [1, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000, 10000, 50000, 100000]
SENDERS = ["USD","GBP","EUR","AED","SAR","CAD","AUD","QAR","KWD","OMR","BHD","MYR","SGD","CNY","TRY","JPY"]
FAWAZ = ["https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@%s/v1/currencies/usd.json",
         "https://%s.currency-api.pages.dev/v1/currencies/usd.json"]


# ---------------------------------------------------------------- helpers
def jload(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def get(url, t=25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RateNowBot"})
    return json.load(urllib.request.urlopen(req, timeout=t))

def w(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)

def fmt(x):
    if x >= 1000: return f"{x:,.2f}"
    if x >= 100: return f"{x:,.3f}"
    if x >= 1: return f"{x:,.4f}"
    return f"{x:.6f}"

def money(x):
    return f"{x:,.2f}" if x >= 1 else f"{x:.4f}"

def slug(a, b): return f"{a.lower()}-to-{b.lower()}"
def hub(a): return f"{a.lower()}-exchange-rates"
def allowed(a, b): return a != b and b not in METALS and not (a in METALS and b in METALS)
def jd(o): return json.dumps(o, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")


# ---------------------------------------------------------------- data
def fetch_latest():
    rates = {}
    try:
        d = get("https://open.er-api.com/v6/latest/USD")
        if d.get("result") == "success":
            rates = {c: float(d["rates"][c]) for c in CUR if c in d["rates"]}
    except Exception as e:
        print("er-api failed:", e)
    missing = [c for c in CUR if c not in rates]
    if missing:
        for tpl in FAWAZ:
            try:
                fz = get(tpl % "latest")["usd"]
                for c in missing:
                    if fz.get(c.lower()): rates[c] = float(fz[c.lower()])
                break
            except Exception as e:
                print("fawaz latest failed:", e)
    return rates if len(rates) > 20 else None

def bootstrap(hist, days=45):
    fails = 0
    for i in range(days, 0, -1):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        if d in hist: continue
        got = None
        for tpl in FAWAZ:
            try:
                fz = get(tpl % d, 15)["usd"]
                got = {c: float(fz[c.lower()]) for c in CUR if fz.get(c.lower())}
                break
            except Exception:
                continue
        if got and len(got) > 20:
            hist[d] = got; fails = 0
        else:
            fails += 1
            if fails >= 5: break

def synth(base):
    rnd = random.Random(7); hist = {}
    for i in range(60, 0, -1):
        d = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        hist[d] = {c: v * (1 + 0.02 * math.sin(i / 6.0 + len(c)) + rnd.uniform(-0.004, 0.004)) for c, v in base.items()}
    return hist


# ---------------------------------------------------------------- analysis
def insight(a, b, ds, vs):
    n = len(vs)
    if n < 5: return None
    cur = vs[-1]; past = vs[:-1]
    pct = round(100 * sum(1 for v in past if v <= cur) / len(past))
    hi, lo = max(vs), min(vs); avg = sum(vs) / n
    ref = vs[-8] if n >= 8 else vs[0]
    tr = (cur - ref) / ref * 100
    label = ("Very favourable" if pct >= 80 else "Favourable" if pct >= 60 else "Neutral" if pct >= 40
             else "Unfavourable" if pct >= 20 else "Very unfavourable")
    best = ds[vs.index(hi)]
    text = (f"Today's {a} to {b} rate is higher than {pct}% of the last {n-1} daily readings, so timing for converting "
            f"{a} into {b} looks {label.lower()}. The range over this period is {fmt(lo)} to {fmt(hi)} "
            f"(average {fmt(avg)}; the best day was {best}). The last-week trend is "
            f"{'up' if tr >= 0 else 'down'} {abs(tr):.2f}%. This is a description of past data, not a prediction or advice.")
    return dict(pct=pct, hi=hi, lo=lo, avg=avg, tr=tr, label=label, text=text, n=n, best=best, cur=cur)

def chart(ds, vs):
    n = len(vs)
    if n < 2: return ""
    W, H, P = 640, 200, 30
    lo, hi = min(vs), max(vs); span = (hi - lo) or abs(lo) * 0.001 or 1
    pts = [(P + i * (W - 2 * P) / (n - 1), H - P - (v - lo) / span * (H - 2 * P)) for i, v in enumerate(vs)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{pts[0][0]:.1f},{H-P} " + line + f" {pts[-1][0]:.1f},{H-P}"
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Rate history chart">'
            f'<polygon points="{area}" class="ca"/><polyline points="{line}" class="cl" fill="none"/>'
            f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4" class="cd"/>'
            f'<text x="{P}" y="14" class="ct">{fmt(hi)}</text><text x="{P}" y="{H-8}" class="ct">{fmt(lo)}</text>'
            f'<text x="{W-P}" y="{H-8}" text-anchor="end" class="ct">{ds[0]} to {ds[-1]}</text></svg>')


# ---------------------------------------------------------------- UI pieces
def adblock():
    c, s = CFG.get("adsense_client", ""), CFG.get("adsense_slot", "")
    if not c or not s: return ""
    return (f'<div class="ad"><ins class="adsbygoogle" style="display:block" data-ad-client="{c}" '
            f'data-ad-slot="{s}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>')

def affbox():
    u = CFG.get("affiliate_url", "")
    if not u: return ""
    t = escape(CFG.get("affiliate_text", "Send money abroad with low fees"))
    return f'<p class="aff"><b>{t}.</b> <a href="{escape(u)}" rel="sponsored noopener" target="_blank">See the offer</a> (sponsored link)</p>'

MARK = ('<svg viewBox="0 0 32 32" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" '
        'stroke-linecap="round" stroke-linejoin="round"><circle cx="16" cy="16" r="12.5"/><path d="M9.5 13h12l-3.3-3.3M22.5 19h-12l3.3 3.3"/></svg>')
ICON_THEME = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="2"/>'
              '<path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>')
ICON_SWAP = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h15l-4-4M20 16H5l4 4"/></svg>')
ICON_MIC = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>')

def spark(vs, n=30):
    v = vs[-n:]
    if len(v) < 2: return '<svg class="spark" aria-hidden="true"></svg>'
    lo, hi = min(v), max(v); span = (hi - lo) or 1
    pts = " ".join(f"{1 + i * 90 / (len(v) - 1):.1f},{26 - (x - lo) / span * 24:.1f}" for i, x in enumerate(v))
    return (f'<svg class="spark" viewBox="0 0 92 28" aria-hidden="true"><polyline points="{pts}" fill="none" '
            'stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/></svg>')

def badge(pct, suffix=""):
    if pct is None: return ""
    cls = "flat" if abs(pct) < 0.005 else ("up" if pct > 0 else "down")
    return f'<span class="chg {cls}">{abs(pct):.2f}%{suffix}</span>'

def day_change(vs):
    return (vs[-1] - vs[-2]) / vs[-2] * 100 if len(vs) >= 2 and vs[-2] else None

def guilloche():
    W, H = 1400, 520; out = []
    for i in range(38):
        ph = i * 0.16; pts = []
        for x in range(0, W + 1, 14):
            y = (H / 2 + (i - 19) * 6.2 + (34 + (i % 7) * 4) * math.sin(x / 88.0 + ph)
                 + 70 * math.sin(x / 330.0 + ph * 0.55) * math.cos(i * 0.21))
            pts.append(f"{x},{y:.1f}")
        out.append(f'<polyline points="{" ".join(pts)}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" fill="none" '
            f'stroke="#a8e0c6" stroke-opacity=".11" stroke-width="1">{"".join(out)}</svg>')

def make_png(size):
    bg, fg = (19, 66, 52), (255, 255, 255)
    rows = []; cx = cy = (size - 1) / 2.0
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / size
            col = fg if 0.30 < d < 0.37 else bg
            if abs(y - cy) < size * 0.035 and abs(x - cx) < size * 0.17: col = fg
            row += bytes(col)
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def shell(title, desc, path, body, up="../", lang="en", alts=None, schema=None, has_gold=False, noindex=False, popular=None):
    c = CFG.get("adsense_client", ""); ga = CFG.get("ga_id", "")
    head = ['<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            f"<title>{escape(title)}</title>", f'<meta name="description" content="{escape(desc)}">',
            f'<link rel="canonical" href="{SITE}/{path}">', '<meta name="theme-color" content="#134234">',
            f'<link rel="manifest" href="{up}manifest.json">', f'<link rel="icon" href="{up}icon.svg" type="image/svg+xml">',
            f'<link rel="preload" href="{up}fonts/bricolage.woff2" as="font" type="font/woff2" crossorigin>',
            f'<link rel="preload" href="{up}fonts/public-sans.woff2" as="font" type="font/woff2" crossorigin>',
            f'<link rel="stylesheet" href="{up}ratenow.css">',
            f'<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(desc)}">',
            '<script>try{var t=JSON.parse(localStorage.getItem("rn_theme"));if(t)document.documentElement.setAttribute("data-theme",t)}catch(e){}</script>']
    if noindex: head.append('<meta name="robots" content="noindex">')
    for hl, hu in (alts or []):
        head.append(f'<link rel="alternate" hreflang="{hl}" href="{SITE}/{hu}">')
    if schema: head.append(f'<script type="application/ld+json">{jd(schema)}</script>')
    if c: head.append(f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={c}" crossorigin="anonymous"></script>')
    if ga: head.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{ga}");</script>')
    nav = [("Rates", "index.html", ""), ("Send money", "send-money-to-pakistan/", "send-money-to-pakistan/")]
    if has_gold: nav.append(("Gold", "gold-rate-in-pakistan/", "gold-rate-in-pakistan/"))
    nav += [("Movers", "today/", "today/"), ("API", "api/", "api/")]
    CURATTR = ' aria-current="page"'
    navh = "".join(f'<a href="{up}{u}"{CURATTR if path == p else ""}>{t}</a>' for t, u, p in nav)
    tg = CFG.get("telegram_channel_url", "")
    pop = "".join(f'<li><a href="{up}{slug(a,b)}/">{a} to {b}</a></li>' for a, b in (popular or []))
    tools = (f'<li><a href="{up}send-money-to-pakistan/">Send money to Pakistan</a></li>'
             + (f'<li><a href="{up}gold-rate-in-pakistan/">Gold rate in Pakistan</a></li>' if has_gold else "")
             + f'<li><a href="{up}today/">Today\'s movers</a></li><li><a href="{up}widget/">Free widget</a></li>')
    site = (f'<li><a href="{up}about.html">About</a></li><li><a href="{up}privacy.html">Privacy</a></li>'
            f'<li><a href="{up}api/">Free API</a></li><li><a href="{up}rss.xml">RSS</a></li>'
            + (f'<li><a href="{escape(tg)}" rel="noopener">Telegram channel</a></li>' if tg else ""))
    dr = ' dir="rtl"' if lang == "ur" else ""
    return (f'<!doctype html><html lang="{lang}"{dr}><head>{"".join(head)}</head><body>'
            f'<header class="top"><div class="wrap bar"><a class="brand" href="{up}index.html">{MARK}<span>{escape(NAME)}</span></a>'
            f'<nav class="nav" aria-label="Main">{navh}</nav>'
            f'<button id="theme" class="icon" aria-label="Switch between light and dark">{ICON_THEME}</button></div></header>'
            f'<main>{body}</main>'
            f'<footer class="foot"><div class="wrap fcols"><div><a class="brand" href="{up}index.html">{MARK}<span>{escape(NAME)}</span></a>'
            f'<p class="note">Daily exchange rates, history and tools for people who send, save and trade across currencies.</p></div>'
            f'<div><h4>Popular rates</h4><ul>{pop}</ul></div><div><h4>Tools</h4><ul>{tools}</ul></div><div><h4>Site</h4><ul>{site}</ul></div>'
            f'<p class="fine">Rates are mid-market values updated daily, for information only. Banks and exchange shops add their own margin. '
            f'Nothing here is financial advice. &copy; {datetime.date.today().year} {escape(NAME)}</p></div></footer>'
            f'<script>window.UP="{up}";</script><script src="{up}ratenow.js" defer></script></body></html>')

def wrap(inner, cls="page"): return f'<div class="{cls}"><div class="wrap">{inner}</div></div>'


# ---------------------------------------------------------------- main
def main():
    os.makedirs(DATA, exist_ok=True)
    hist = jload(os.path.join(DATA, "history.json"), {})
    if SAMPLE_MODE:
        rates = dict(SAMPLE); hist = synth(rates)
    else:
        rates = fetch_latest()
        if rates is None:
            if not hist: sys.exit("No rates available")
            rates = hist[sorted(hist)[-1]]
        if len(hist) < 10: bootstrap(hist)
    hist[TODAY] = rates
    for k in sorted(hist)[:-90]: del hist[k]
    if not SAMPLE_MODE:
        json.dump(hist, open(os.path.join(DATA, "history.json"), "w"), separators=(",", ":"))

    dates_all = sorted(hist)
    codes = [c for c in CUR if c in rates]
    has_gold = "XAU" in rates and "PKR" in rates
    popset = set(POPULAR)
    FOOT_POP = [("USD","PKR"),("GBP","PKR"),("EUR","PKR"),("AED","PKR"),("SAR","PKR"),("USD","INR")]
    foot_pop = [p for p in FOOT_POP if p[0] in rates and p[1] in rates]

    def rt(rs, a, b): return rs[b] / rs[a]
    def series(a, b):
        ds = [d for d in dates_all[-60:] if a in hist[d] and b in hist[d]]
        return ds, [rt(hist[d], a, b) for d in ds]
    def S(title, desc, path, body, **kw):
        return shell(title, desc, path, body, has_gold=has_gold, popular=foot_pop, **kw)

    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy(os.path.join(ASSETS, "ratenow.css"), os.path.join(OUT, "ratenow.css"))
    shutil.copy(os.path.join(ASSETS, "ratenow.js"), os.path.join(OUT, "ratenow.js"))
    shutil.copytree(os.path.join(ASSETS, "fonts"), os.path.join(OUT, "fonts"))
    w("guilloche.svg", guilloche())
    w("sw.js", open(os.path.join(ASSETS, "sw.js"), encoding="utf-8").read().replace("%V%", TODAY))
    for s in (192, 512):
        with open(os.path.join(OUT, f"icon-{s}.png"), "wb") as f: f.write(make_png(s))
    w("icon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#134234"/>'
      '<g fill="none" stroke="#fff" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="32" cy="32" r="21"/>'
      '<path d="M20 27h24l-6-6M44 37H20l6 6"/></g></svg>')
    w("manifest.json", jd({"name": NAME, "short_name": NAME, "start_url": "./", "scope": "./", "display": "standalone",
        "theme_color": "#134234", "background_color": "#f4f6f5",
        "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]}))
    w("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    key = CFG.get("indexnow_key", "")
    if key: w(f"{key}.txt", key)

    rjson = {"date": TODAY, "rates": {c: rates[c] for c in codes}, "names": {c: CUR[c] for c in codes},
             "metals": sorted(METALS & set(codes)), "defaultRupee": CFG.get("default_rupee", "PKR")}
    w("data/rates.json", jd(rjson))
    ratestag = f'<script type="application/json" id="rates">{jd(rjson)}</script>'
    urls = [f"{SITE}/"]

    # ---- movers (vs PKR) + log
    movers = []
    if "PKR" in rates and len(dates_all) > 1:
        pd_ = hist[dates_all[-2]]
        for c in codes:
            if c == "PKR" or c in METALS or c not in pd_ or "PKR" not in pd_: continue
            now, prev = rates["PKR"] / rates[c], pd_["PKR"] / pd_[c]
            movers.append((c, now, (now - prev) / prev * 100))
        movers.sort(key=lambda x: -x[2])
    mlog = jload(os.path.join(DATA, "movers.json"), [])
    if movers and not SAMPLE_MODE:
        mlog = [m for m in mlog if m["date"] != TODAY] + [{"date": TODAY, "up": movers[:3], "down": movers[-3:]}]
        mlog = mlog[-14:]
        json.dump(mlog, open(os.path.join(DATA, "movers.json"), "w"))

    # ---- pair pages
    count = 0
    for a in codes:
        for b in codes:
            if not allowed(a, b): continue
            r = rates[b] / rates[a]
            ds, vs = series(a, b)
            ins = insight(a, b, ds, vs)
            na, nb = CUR[a], CUR[b]
            p1 = day_change(vs)
            link_amt = (a, b) in popset
            rows = "".join(
                "<tr><td>" + (f'<a href="../{x}-{slug(a,b)}/">{x:,} {a}</a>' if link_amt and x in AMT2 else f"{x:,} {a}") +
                f'</td><td class="n">{money(x*r)} {b}</td></tr>' for x in AMOUNTS)
            stats = ""
            for wdw in (7, 30, 60):
                if len(vs) >= wdw:
                    seg = vs[-wdw:]
                    stats += (f'<tr><td>{wdw} days</td><td class="n">{fmt(max(seg))}</td><td class="n">{fmt(min(seg))}</td>'
                              f'<td class="n">{fmt(sum(seg)/len(seg))}</td><td class="n">{badge((seg[-1]-seg[0])/seg[0]*100)}</td></tr>')
            stats_h = (f'<div class="tblwrap"><table class="tbl"><thead><tr><th>Period</th><th class="n">High</th><th class="n">Low</th><th class="n">Average</th><th class="n">Change</th></tr></thead><tbody>{stats}</tbody></table></div>'
                       if stats else '<p class="note">History builds up automatically every day. Statistics appear here after the first week.</p>')
            timing = ""
            if ins:
                span = ins["hi"] - ins["lo"]
                pos = 50 if span <= 0 else (ins["cur"] - ins["lo"]) / span * 100
                timing = (f'<section class="sec"><h2>Is it a good time to convert?</h2>'
                          f'<p class="verdict">{ins["label"]}: today beats {ins["pct"]}% of the last {ins["n"]-1} days.</p>'
                          f'<div class="meter" role="img" aria-label="Today sits {pos:.0f}% of the way between the period low and high">'
                          f'<div class="mtrack"><span class="mmark" style="left:{pos:.1f}%"></span></div>'
                          f'<div class="mlab"><span>Low {fmt(ins["lo"])}</span><span>High {fmt(ins["hi"])}</span></div></div>'
                          f'<p>Average over the period is {fmt(ins["avg"])}. The best day was {ins["best"]}. '
                          f'Over the last week the rate moved {"up" if ins["tr"] >= 0 else "down"} {abs(ins["tr"]):.2f}%.</p>'
                          f'<p class="note">This describes past data. It is not a prediction or advice.</p></section>')
            others = [x for x in codes if x not in (a, b) and allowed(a, x)][:8]
            others2 = [x for x in codes if x not in (a, b) and allowed(x, b)][:8]
            rel1 = "".join(f'<li><a href="../{slug(a,x)}/"><span>{a} to {x}</span><small>{fmt(rates[x]/rates[a])}</small></a></li>' for x in others)
            rel2 = "".join(f'<li><a href="../{slug(x,b)}/"><span>{x} to {b}</span><small>{fmt(rates[b]/rates[x])}</small></a></li>' for x in others2)
            alts = None; urlnk = ""
            if "PKR" in (a, b) and not ({a, b} & METALS):
                urlnk = f'<p><a href="../ur/{slug(a,b)}/" hreflang="ur" lang="ur">اردو میں دیکھیں</a></p>'
                alts = [("en", f"{slug(a,b)}/"), ("ur", f"ur/{slug(a,b)}/")]
            tm = ""
            if len(vs) >= 3:
                tm = (f'<h3>What if you had converted earlier?</h3><p><label>Amount in {a} <input id="tmamt" type="number" value="100" min="0" step="any" style="max-width:130px"></label></p>'
                      f'<p><label>Days back: <b id="tmlab"></b><br><input id="tm" type="range" min="0" max="{len(vs)-1}" value="{min(7, len(vs)-1)}" style="height:auto;padding:0;border:0;max-width:420px"></label></p>'
                      f'<p id="tmout"></p>')
            if a in METALS:
                nm = na.split(" (")[0]
                title = f"{nm} Price in {nb} Today ({a} to {b})"
                desc = f"1 troy ounce of {nm.lower()} costs {fmt(r)} {b} today. Price history, converter and rate alerts."
                h1 = f"{nm} price in {nb}"
            elif b == "PKR":
                title = f"{na} Rate in Pakistan Today ({a} to PKR)"
                desc = f"1 {a} = {fmt(r)} PKR today. {na} to Pakistani Rupee converter with history chart, fee calculator and rate alerts."
                h1 = f"{na} to Pakistani Rupee"
            else:
                title = f"{a} to {b} Today: {na} to {nb} Exchange Rate"
                desc = f"1 {a} = {fmt(r)} {b} today. {na} to {nb} converter with history chart, fee calculator and rate alerts."
                h1 = f"{na} to {nb}"
            faq = [(f"What is the {a} to {b} rate today?", f"Today 1 {na} equals {fmt(r)} {nb}."),
                   (f"How much is 100 {a} in {b}?", f"100 {a} is about {money(100*r)} {b}."),
                   (f"How much is 1 {b} in {a}?", f"1 {b} is about {fmt(1/r)} {a}."),
                   ("Where do these rates come from?", "They are mid-market rates refreshed daily. Banks and money changers add their own margin, so the rate you actually get can differ. Use the margin field above to see the real amount.")]
            schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": t}} for q, t in faq]}
            faqh = "".join(f"<dt>{escape(q)}</dt><dd>{escape(t)}</dd>" for q, t in faq)
            pd = {"a": a, "b": b, "r": r, "d": ds, "v": [float(f"{v:.8g}") for v in vs]}
            rng = "".join(f'<button type="button" data-range="{k}" aria-pressed="false">{k} days</button>' for k in (7, 30, 60))
            body = f"""<section class="phero"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Rates</a><span>/</span><a href="../{hub(a)}/">{a}</a><span>/</span><span>{a} to {b}</span></nav>
<h1>{h1}</h1><div class="prate"><span class="pnum">{fmt(r)}</span><span class="punit">{b}</span>{badge(p1, " today")}</div>
<p class="pmeta">1 {a} buys {fmt(r)} {b}. Updated {TODAY}.</p></div></section>
<div class="page"><div class="wrap cols"><div>
<section class="sec"><h2>Convert {a} to {b}</h2><div class="calc">
<label class="f">Amount in {a}<input id="amt" type="number" value="1" min="0" step="any"></label>
<div class="f">Result in {b}<div class="big"><output id="out"></output><span>{b}</span></div></div>
<label class="f">Bank or exchange margin (%)<input id="fee" type="number" value="0" min="0" max="25" step="0.1"></label>
<div class="f">After the margin you receive<div class="big"><output id="feeout"></output><span>{b}</span></div></div>
<p class="note wide">The margin costs you <span id="feecost"></span> {b}. Ask your bank or exchange shop for their margin, then enter it here.</p></div></section>
{adblock()}
<section class="sec"><h2>{a} to {b} history</h2><div class="ranges" role="group" aria-label="Chart range">{rng}</div>
<div class="chartbox" id="chart">{chart(ds, vs)}</div>
<h3>Statistics</h3>{stats_h}</section>
{timing}
<section class="sec"><h2>Tools</h2>{tm}
<h3>Rate alert</h3><div class="row"><span>Tell me when 1 {a} is</span><select id="aldir" style="width:auto"><option value="above">above</option><option value="below">below</option></select>
<input id="alt" type="number" step="any" placeholder="{fmt(r)}" style="width:140px" aria-label="Target rate"><button id="albtn" class="btn" type="button">Set alert</button></div>
<p id="almsg" class="note">Alerts check the rate when this site is open. Add the site to your phone's home screen to open it faster.</p><div id="allist"></div></section>
<section class="sec"><h2>{a} to {b} conversion table</h2><div class="tblwrap"><table class="tbl"><thead><tr><th>{a}</th><th class="n">{b}</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="sec"><h2>Common questions</h2><dl class="faq">{faqh}</dl></section>
</div><aside class="side"><div class="row"><button id="fav" class="btn alt" type="button">Save pair</button><button id="share" class="btn alt" type="button">Share</button></div>
{affbox()}<h3>More {a} rates</h3><ul class="plain">{rel1}</ul><h3>More rates to {b}</h3><ul class="plain">{rel2}</ul>
<h3>More</h3><p><a href="../{hub(a)}/">All {na} rates</a></p>{urlnk}<p><a href="../widget/">Put this converter on your website</a></p></aside></div></div>
<script type="application/json" id="pd">{jd(pd)}</script>"""
            w(f"{slug(a,b)}/index.html", S(title, desc, f"{slug(a,b)}/", body, alts=alts, schema=schema))
            urls.append(f"{SITE}/{slug(a,b)}/"); count += 1

    # ---- long-tail amount pages for popular pairs
    ac = 0
    for a, b in POPULAR:
        if a not in rates or b not in rates: continue
        r = rates[b] / rates[a]; na, nb = CUR[a], CUR[b]
        ds, vs = series(a, b); p1 = day_change(vs)
        for x in AMT2:
            near = [y for y in AMT2 if y != x and 0.1 <= y / x <= 10][:8]
            nrows = "".join(f'<tr><td><a href="../{y}-{slug(a,b)}/">{y:,} {a}</a></td><td class="n">{money(y*r)} {b}</td></tr>' for y in near)
            body = f"""<section class="phero"><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Rates</a><span>/</span><a href="../{slug(a,b)}/">{a} to {b}</a><span>/</span><span>{x:,} {a}</span></nav>
<h1>{x:,} {na} in {nb}</h1><div class="prate"><span class="pnum">{money(x*r)}</span><span class="punit">{b}</span>{badge(p1, " today")}</div>
<p class="pmeta">{x:,} {a} at today's rate of {fmt(r)} {b}. Updated {TODAY}.</p></div></section>
{wrap(f'''<section class="sec"><h2>Another amount</h2><div class="calc"><label class="f">Amount in {a}<input id="amt" type="number" value="{x}" min="0" step="any"></label>
<div class="f">Result in {b}<div class="big"><output id="out"></output><span>{b}</span></div></div></div>
<p>{x:,} {b} would be about {money(x/r)} {a}.</p></section>{adblock()}
<section class="sec"><h2>Nearby amounts</h2><div class="tblwrap"><table class="tbl"><thead><tr><th>{a}</th><th class="n">{b}</th></tr></thead><tbody>{nrows}</tbody></table></div></section>
<p><a href="../{slug(a,b)}/">{a} to {b}: chart, timing and alerts</a><br><a href="../{slug(b,a)}/">{b} to {a}</a></p>''')}
<script type="application/json" id="pd">{jd({"a": a, "b": b, "r": r})}</script>"""
            title = f"{x:,} {a} to {b}: {x:,} {na} in {nb} Today"
            desc = f"{x:,} {a} = {money(x*r)} {b} today. Convert {x:,} {na} to {nb} at the latest exchange rate."
            w(f"{x}-{slug(a,b)}/index.html", S(title, desc, f"{x}-{slug(a,b)}/", body))
            urls.append(f"{SITE}/{x}-{slug(a,b)}/"); ac += 1

    # ---- Urdu pages (PKR pairs)
    uc = 0
    for c in codes:
        if c == "PKR": continue
        for a, b in ((c, "PKR"), ("PKR", c)):
            if not allowed(a, b): continue
            r = rates[b] / rates[a]; ds, vs = series(a, b); p1 = day_change(vs)
            rows = "".join(f'<tr><td>{x:,} {a}</td><td class="n">{money(x*r)} {b}</td></tr>' for x in AMOUNTS)
            body = f"""<section class="phero"><div class="wrap"><h1>{UR[a]} کا ریٹ آج</h1>
<div class="prate"><span class="pnum">{fmt(r)}</span><span class="punit">{b}</span>{badge(p1, " آج")}</div>
<p class="pmeta">1 {a} = {fmt(r)} {b}۔ تاریخ: {TODAY}</p></div></section>
{wrap(f'''<section class="sec"><h2>رقم تبدیل کریں</h2><div class="calc"><label class="f">{a} میں رقم<input id="amt" type="number" value="1" min="0" step="any"></label>
<div class="f">{b} میں نتیجہ<div class="big"><output id="out"></output><span>{b}</span></div></div></div></section>{adblock()}
<section class="sec"><div class="tblwrap"><table class="tbl"><thead><tr><th>{a}</th><th class="n">{b}</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<p><a href="../../{slug(a,b)}/" lang="en" dir="ltr">View in English: chart, alerts and tools</a></p>''')}
<script type="application/json" id="pd">{jd({"a": a, "b": b, "r": r})}</script>"""
            title = f"{UR[a]} کا ریٹ آج ({a} to {b}) | {UR[b]} میں"
            desc = f"آج 1 {a} = {fmt(r)} {b}۔ {UR[a]} سے {UR[b]} کنورٹر اور ریٹ ٹیبل۔"
            w(f"ur/{slug(a,b)}/index.html", S(title, desc, f"ur/{slug(a,b)}/", body, up="../../", lang="ur",
                alts=[("en", f"{slug(a,b)}/"), ("ur", f"ur/{slug(a,b)}/")]))
            urls.append(f"{SITE}/ur/{slug(a,b)}/"); uc += 1

    # ---- hubs
    for a in codes:
        trs = "".join(f'<tr data-r="{rates[x]/rates[a]}"><td><a href="../{slug(a,x)}/">{x}</a><small>{CUR[x]}</small></td><td class="n v">{fmt(rates[x]/rates[a])}</td></tr>'
                      for x in codes if allowed(a, x))
        body = wrap(f"""<h1>{CUR[a]} ({a}) exchange rates</h1><p>Enter an amount to see it in every currency at once.</p>
<div class="calc" style="max-width:420px"><label class="f">Amount in {a}<input id="hamt" type="number" value="1" min="0" step="any"></label></div>{adblock()}
<div class="tblwrap"><table class="tbl scale"><thead><tr><th>Currency</th><th class="n">Value</th></tr></thead><tbody>{trs}</tbody></table></div>""")
        w(f"{hub(a)}/index.html", S(f"{CUR[a]} ({a}) Exchange Rates Today", f"{CUR[a]} against {len(codes)-1} currencies: live multi-converter, updated daily.", f"{hub(a)}/", body))
        urls.append(f"{SITE}/{hub(a)}/")

    # ---- today / movers
    if movers:
        def mrow(m): return (f'<tr><td><a href="../{slug(m[0],"PKR")}/">{m[0]}</a><small>{CUR[m[0]]}</small></td>'
                             f'<td class="n">{fmt(m[1])} PKR</td><td class="n">{badge(m[2])}</td></tr>')
        head = '<thead><tr><th>Currency</th><th class="n">1 unit in rupees</th><th class="n">Today</th></tr></thead>'
        body = wrap(f"""<h1>Currency movers, {TODAY}</h1><p>How each currency moved against the Pakistani rupee since yesterday.</p>{adblock()}
<section class="sec"><h2>Biggest gainers</h2><div class="tblwrap"><table class="tbl">{head}<tbody>{''.join(mrow(m) for m in movers[:5])}</tbody></table></div></section>
<section class="sec"><h2>Biggest decliners</h2><div class="tblwrap"><table class="tbl">{head}<tbody>{''.join(mrow(m) for m in movers[::-1][:5])}</tbody></table></div></section>
<section class="sec"><h2>All currencies</h2><div class="tblwrap"><table class="tbl">{head}<tbody>{''.join(mrow(m) for m in movers)}</tbody></table></div></section>""")
    else:
        body = wrap("<h1>Currency movers</h1><p>Daily movers appear here after two days of data are collected.</p>")
    w("today/index.html", S(f"Currency Movers Today, {TODAY}", "Which currencies gained or lost against the Pakistani rupee today.", "today/", body))
    urls.append(f"{SITE}/today/")
    items = "".join(
        f"<item><title>Currency movers {m['date']}</title><link>{SITE}/today/</link><guid isPermaLink=\"false\">{m['date']}</guid>"
        f"<description>{escape('Up: ' + ', '.join(f'{x[0]} {x[2]:+.2f}%' for x in m['up']) + ' | Down: ' + ', '.join(f'{x[0]} {x[2]:+.2f}%' for x in m['down']))}</description></item>"
        for m in reversed(mlog))
    w("rss.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{escape(NAME)} movers</title><link>{SITE}/</link><description>Daily currency movers against the rupee</description>{items}</channel></rss>')

    # ---- send money
    if "PKR" in rates:
        opts = "".join(f'<option value="{c}">{c}: {CUR[c]}</option>' for c in SENDERS if c in rates)
        trs = ""
        for c in SENDERS:
            if c in rates and c != "PKR":
                _, v = series(c, "PKR")
                trs += (f'<tr><td><a href="../{slug(c,"PKR")}/">{c}</a><small>{CUR[c]}</small></td><td class="n">{fmt(rates["PKR"]/rates[c])} PKR</td>'
                        f'<td class="n">{badge(day_change(v))}</td></tr>')
        body = wrap(f"""<h1>Send money to Pakistan</h1><p>See how many rupees your family receives. Enter the margin your bank or app charges to get the real amount.</p>
<section class="sec"><div class="calc"><label class="f">You send<input id="samt" type="number" value="500" min="0" step="any"></label>
<label class="f">Currency<select id="sfrom">{opts}</select></label>
<label class="f">Bank or app margin (%)<input id="sfee" type="number" value="2" min="0" max="25" step="0.1"></label>
<div class="f">Your family receives<div class="big"><output id="sout"></output><span>PKR</span></div></div>
<p class="note wide">At the mid-market rate that would be <span id="smid"></span> PKR. The margin costs <span id="scost"></span> PKR.</p></div></section>
{affbox()}{adblock()}<section class="sec"><h2>Today's rates to the rupee</h2><div class="tblwrap"><table class="tbl"><thead><tr><th>Currency</th><th class="n">1 unit buys</th><th class="n">Today</th></tr></thead><tbody>{trs}</tbody></table></div></section>{ratestag}""")
        w("send-money-to-pakistan/index.html", S("Send Money to Pakistan: Rates and Fee Calculator", "Today's rates to PKR from USD, GBP, EUR, AED, SAR and more, with a calculator that shows what your family really receives after fees.", "send-money-to-pakistan/", body))
        urls.append(f"{SITE}/send-money-to-pakistan/")

    # ---- gold
    tola_pkr = None
    if has_gold:
        gd = {c: rates[c] / rates["XAU"] for c in codes if c not in METALS}
        gcur = "".join(f'<option value="{c}"{" selected" if c=="PKR" else ""}>{c}</option>' for c in gd)
        opk = gd["PKR"]; tola_pkr = opk / 31.1034768 * 11.6638038
        _, gv = series("XAU", "PKR"); gp = day_change(gv)
        def line(k): return (f'<tr><td>{k}K</td><td class="n">{money(opk/31.1034768*k/24)}</td><td class="n">{money(opk/31.1034768*k/24*11.6638038)}</td>'
                             f'<td class="n">{money(opk/31.1034768*k/24*10)}</td></tr>')
        body = f"""<section class="phero"><div class="wrap"><h1>Gold rate in Pakistan today</h1>
<div class="prate"><span class="pnum">{tola_pkr:,.0f}</span><span class="punit">PKR per tola (24K)</span>{badge(gp, " today")}</div>
<p class="pmeta">International spot price converted to rupees on {TODAY}. Local jewellers add premiums, making charges and taxes, so shop prices differ.</p></div></section>
{wrap(f'''<section class="sec"><h2>Price by purity</h2><div class="tblwrap"><table class="tbl"><thead><tr><th>Purity</th><th class="n">Per gram</th><th class="n">Per tola</th><th class="n">10 grams</th></tr></thead>
<tbody>{line(24)}{line(22)}{line(21)}{line(18)}</tbody></table></div><p class="note">All values in PKR. One tola is 11.664 grams.</p></section>{adblock()}
<section class="sec"><h2>Gold value calculator</h2><div class="calc"><label class="f">Weight<input id="gw" type="number" value="1" min="0" step="any"></label>
<label class="f">Unit<select id="gu"><option value="11.6638038">tola</option><option value="1">gram</option><option value="31.1034768">ounce</option></select></label>
<label class="f">Purity<select id="gk"><option value="24">24K</option><option value="22" selected>22K</option><option value="21">21K</option><option value="18">18K</option></select></label>
<label class="f">Currency<select id="gc">{gcur}</select></label>
<label class="f">Making charges (%)<input id="gm" type="number" value="0" min="0" max="50" step="0.5"></label>
<div class="f">Value<div class="big"><output id="gout"></output></div></div></div></section>
<p><a href="../xau-to-pkr/">Gold price history and alerts</a></p>''')}
<script type="application/json" id="gd">{jd(gd)}</script>"""
        w("gold-rate-in-pakistan/index.html", S("Gold Rate in Pakistan Today: Per Tola, Gram and Ounce", "Today's gold price in Pakistan per tola, gram and ounce for 24K, 22K, 21K and 18K, with a gold value calculator.", "gold-rate-in-pakistan/", body))
        urls.append(f"{SITE}/gold-rate-in-pakistan/")

    # ---- API + widget
    w("api/latest.json", jd({"base": "USD", "date": TODAY, "rates": rjson["rates"]}))
    for a in codes:
        w(f"api/{a.lower()}.json", jd({"base": a, "date": TODAY, "rates": {x: rates[x] / rates[a] for x in codes if x != a}}))
    body = wrap(f"""<h1>Free currency API</h1><p>No key, no sign-up, no limits. Updated daily and open to browser requests. Please link back to {escape(NAME)} if you use it.</p>
<section class="sec"><h2>Endpoints</h2><p><code>{SITE}/api/latest.json</code> returns rates per 1 USD.<br><code>{SITE}/api/pkr.json</code> returns rates per 1 of any currency code (usd, eur, gbp, aed and the rest).</p>
<pre>fetch("{SITE}/api/usd.json").then(r =&gt; r.json()).then(d =&gt; console.log(d.rates.PKR))</pre></section>
<section class="sec"><h2>Currencies</h2><p>{", ".join(codes)}</p></section>""")
    w("api/index.html", S("Free Currency Exchange Rate API", "Free daily currency exchange rate JSON API with no key.", "api/", body))
    urls.append(f"{SITE}/api/")
    opts = "".join(f'<option value="{c}">{c}</option>' for c in codes if c not in METALS)
    body = wrap(f"""<h1>Free converter widget</h1><p>Add a live currency converter to your website. Choose a pair, copy the code and paste it into your page.</p>
<section class="sec"><div class="calc" style="max-width:420px"><label class="f">From<select id="wf">{opts}</select></label><label class="f">To<select id="wt">{opts}</select></label></div>
<h3>Code</h3><textarea id="wcode" rows="4" readonly></textarea><h3>Preview</h3><iframe id="wprev" title="Widget preview" width="320" height="170" style="border:1px solid var(--line)"></iframe></section>
<script type="application/json" id="wsite">{jd(SITE)}</script>""")
    w("widget/index.html", S("Free Currency Converter Widget for Your Website", "Embed a free live currency converter on your website with one line of code.", "widget/", body))
    urls.append(f"{SITE}/widget/")
    w("embed.html", f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<style>@font-face{{font-family:B;src:url(fonts/bricolage.woff2) format("woff2");font-weight:200 800}}body{{margin:0;font:15px system-ui,sans-serif;padding:12px;background:#fff;color:#14231d}}
input,select{{font-size:15px;padding:7px;border:1px solid #c4cfc9;border-radius:4px;max-width:100%}}b{{font:650 22px B,system-ui;color:#17503f}}a{{font-size:12px;color:#51635b}}</style></head><body>
<div><input id="ea" type="number" value="1" min="0" step="any" style="width:90px"> <select id="ef"></select></div>
<div style="margin:9px 0"><b id="eo"></b> <select id="et"></select></div>
<a id="el" href="{SITE}/" target="_blank" rel="noopener">Rates by {escape(NAME)}</a>
<script>
var R=null,q=new URLSearchParams(location.search);
fetch("data/rates.json").then(function(r){{return r.json()}}).then(function(j){{R=j;var f=document.getElementById("ef"),t=document.getElementById("et");
Object.keys(j.rates).forEach(function(c){{if(j.metals.indexOf(c)<0){{f.add(new Option(c,c));t.add(new Option(c,c))}}}});
f.value=(q.get("from")||"USD").toUpperCase();t.value=(q.get("to")||"PKR").toUpperCase();
var a=q.get("amt");if(a)document.getElementById("ea").value=a;run()}});
function run(){{if(!R)return;var f=document.getElementById("ef").value,t=document.getElementById("et").value,x=parseFloat(document.getElementById("ea").value)||0;
var v=x*R.rates[t]/R.rates[f];document.getElementById("eo").textContent=v.toLocaleString(undefined,{{maximumFractionDigits:v>=1?2:6}});
document.getElementById("el").href="{SITE}/"+f.toLowerCase()+"-to-"+t.toLowerCase()+"/"}}
["ea","ef","et"].forEach(function(i){{document.getElementById(i).addEventListener("input",run)}});
</script></body></html>""")

    # ---- home
    board_codes = [c for c in ("USD", "GBP", "EUR", "AED", "SAR") if c in rates and "PKR" in rates]
    brow = ""
    for c in board_codes:
        ds_, v_ = series(c, "PKR")
        brow += (f'<a class="brow" href="{slug(c,"PKR")}/"><span class="bcode">{c}<small>{CUR[c]}</small></span>'
                 f'<span class="bval">{fmt(rates["PKR"]/rates[c]).rstrip("0").rstrip(".") if rates["PKR"]/rates[c] < 1000 else fmt(rates["PKR"]/rates[c])}</span>'
                 f'{badge(day_change(v_)) or "<span></span>"}<span class="spark">{spark(v_)}</span></a>')
    if tola_pkr:
        _, gv = series("XAU", "PKR")
        brow += (f'<a class="brow" href="gold-rate-in-pakistan/"><span class="bcode">Gold<small>24K, per tola</small></span>'
                 f'<span class="bval">{tola_pkr:,.0f}</span>{badge(day_change(gv)) or "<span></span>"}<span class="spark">{spark(gv)}</span></a>')
    board = (f'<div class="board" role="region" aria-label="Rates against the rupee today"><div class="board-h"><span>1 unit in Pakistani rupees</span><span>{TODAY}</span></div>{brow}</div>'
             if brow else "")
    ex = "".join(f'<button type="button" class="chip" data-q="{q}">{q}</button>' for q in ["500 usd to pkr", "dirham to rupee", "5k pounds in rupees", "gold"])
    rrows = ""
    if "PKR" in rates:
        for c in codes:
            if c == "PKR" or c in METALS: continue
            _, v_ = series(c, "PKR")
            rrows += (f'<tr><td><a href="{slug(c,"PKR")}/">{c}</a><small>{CUR[c]}</small></td><td class="n">{fmt(rates["PKR"]/rates[c])}</td>'
                      f'<td class="n">{badge(day_change(v_))}</td><td class="n"><span class="spark" style="margin-left:auto">{spark(v_)}</span></td></tr>')
    rtable = (f'<section class="sec"><h2>Rupee rates today</h2><div class="tblwrap"><table class="tbl"><thead><tr><th>Currency</th><th class="n">1 unit in PKR</th>'
              f'<th class="n">Today</th><th class="n">30 days</th></tr></thead><tbody>{rrows}</tbody></table></div></section>') if rrows else ""
    tools = (f'<section class="sec"><h2>Tools</h2><ul class="tools">'
             '<li><a href="send-money-to-pakistan/"><b>Send money to Pakistan</b><span>See what your family receives after your bank\'s margin.</span></a></li>'
             + ('<li><a href="gold-rate-in-pakistan/"><b>Gold rate</b><span>Per tola, gram and ounce, with a value calculator.</span></a></li>' if has_gold else "")
             + '<li><a href="today/"><b>Today\'s movers</b><span>Which currencies gained or lost against the rupee.</span></a></li>'
             '<li><a href="usd-to-pkr/"><b>Rate alerts</b><span>Set a target on any pair and get told when it is reached.</span></a></li>'
             '<li><a href="widget/"><b>Widget and API</b><span>Put live rates on your own website, free.</span></a></li></ul></section>')
    allc = "".join(f'<a href="{hub(a)}/">{a}</a>' for a in codes)
    body = f"""<section class="hero"><div class="wrap hero-grid"><div>
<h1>Convert any currency. Type it the way you say it.</h1>
<p class="lede">Daily rates for {len([c for c in codes if c not in METALS])} currencies and gold, with history, fee calculators and rate alerts.</p>
<div class="cmd"><input id="cmd" type="text" placeholder="500 dollar in rupees" autocomplete="off" aria-label="Type a conversion, for example 500 dollar in rupees"><button id="mic" class="mic" type="button" aria-label="Speak your conversion">{ICON_MIC}</button></div>
<div id="cmdout" class="cmdout" aria-live="polite"></div><p class="try">Try {ex}</p></div>{board}</div></section>
<div class="wrap"><section class="conv" aria-label="Currency converter"><label class="f">Amount<input id="bigamt" type="number" value="100" min="0" step="any"></label>
<label class="f">From<select id="bigfrom"></select></label><button id="bigswap" class="swap" type="button" aria-label="Swap currencies">{ICON_SWAP}</button>
<label class="f">To<select id="bigto"></select></label><div class="res"><div id="bigout" class="resv"></div><a id="biglink" href="#">Open this pair</a></div></section></div>
<div class="page" style="padding-top:20px"><div class="wrap"><div id="favs"></div><div id="recent"></div>{rtable}{adblock()}{tools}
<section class="sec"><h2>All currencies</h2><div class="links">{allc}</div></section></div></div>{ratestag}"""
    sch = {"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/"}
    w("index.html", S(f"{NAME}: Currency Converter and Daily Exchange Rates", "Convert currencies in plain words, see daily rates for USD, GBP, EUR, AED, SAR and PKR, and use history charts, fee calculators and rate alerts.", "", body, up="", schema=sch))

    mail = escape(CFG.get("contact_email", "")); ct = f"<p>Contact: {mail}</p>" if mail else ""
    w("about.html", S("About", "About this site", "about.html", wrap(f"<h1>About {escape(NAME)}</h1><p>{escape(NAME)} publishes free, automatically updated currency rates, history charts and tools. Rates are indicative mid-market values and are not financial advice.</p>{ct}"), up=""))
    w("privacy.html", S("Privacy Policy", "Privacy policy", "privacy.html", wrap(
        "<h1>Privacy policy</h1><p>Saved pairs, rate alerts and your colour theme are stored only in your own browser. They are never sent to us.</p>"
        "<p>Third-party vendors, including Google, may use cookies to show ads based on your earlier visits. You can opt out of personalised advertising in Google Ads Settings.</p>"
        f"<p>Rates are for information only and are not financial advice.</p>{ct}"), up=""))
    w("404.html", S("Page not found", "Page not found", "404.html", wrap(f'<h1>Page not found</h1><p>Check the address, or <a href="{SITE}/">go to the rates home page</a>.</p>'), up=SITE + "/", noindex=True))
    urls += [f"{SITE}/about.html", f"{SITE}/privacy.html"]
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls)
    w("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')

    if not SAMPLE_MODE:
        open(os.path.join(DATA, "urls.txt"), "w").write("\n".join(urls))
        lines = [f"{NAME}, {TODAY}"]
        for a, b in [("USD", "PKR"), ("GBP", "PKR"), ("EUR", "PKR"), ("AED", "PKR"), ("SAR", "PKR")]:
            if a in rates and b in rates:
                _, vv = series(a, b); p = day_change(vv)
                lines.append(f"{a}/PKR {fmt(rates[b]/rates[a])}" + (f" ({p:+.2f}%)" if p is not None else ""))
        if movers: lines.append(f"Top gainer vs PKR: {movers[0][0]} {movers[0][2]:+.2f}%")
        lines.append(SITE + "/")
        json.dump({"text": "\n".join(lines)}, open(os.path.join(DATA, "summary.json"), "w"))
    print(f"done: {count} pair pages, {ac} amount pages, {uc} urdu pages, {len(codes)} hubs, {len(urls)} urls, gold={has_gold}")


if __name__ == "__main__":
    main()
