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
    return dict(pct=pct, hi=hi, lo=lo, avg=avg, tr=tr, label=label, text=text, n=n)

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


# ---------------------------------------------------------------- page shell
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
    return f'<div class="box aff"><b>{t}</b> <a href="{escape(u)}" rel="sponsored noopener" target="_blank">Check it out</a> <small>(sponsored link)</small></div>'

def shell(title, desc, path, body, up="../", lang="en", alts=None, schema=None, has_gold=False, noindex=False):
    c = CFG.get("adsense_client", ""); ga = CFG.get("ga_id", "")
    head = [f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            f"<title>{escape(title)}</title>", f'<meta name="description" content="{escape(desc)}">',
            f'<link rel="canonical" href="{SITE}/{path}">', '<meta name="theme-color" content="#0b3d91">',
            f'<link rel="manifest" href="{up}manifest.json">', f'<link rel="icon" href="{up}icon.svg" type="image/svg+xml">',
            f'<link rel="stylesheet" href="{up}style.css">',
            f'<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(desc)}">']
    if noindex: head.append('<meta name="robots" content="noindex">')
    for hl, hu in (alts or []):
        head.append(f'<link rel="alternate" hreflang="{hl}" href="{SITE}/{hu}">')
    if schema: head.append(f'<script type="application/ld+json">{jd(schema)}</script>')
    if c: head.append(f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={c}" crossorigin="anonymous"></script>')
    if ga: head.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{ga}");</script>')
    nav = [("Home", "index.html"), ("Today", "today/"), ("Send money", "send-money-to-pakistan/")]
    if has_gold: nav.append(("Gold", "gold-rate-in-pakistan/"))
    nav += [("API", "api/"), ("Widget", "widget/")]
    navh = "".join(f'<a href="{up}{u}">{t}</a>' for t, u in nav)
    tg = CFG.get("telegram_channel_url", "")
    foot = (f'<a href="{up}about.html">About</a> · <a href="{up}privacy.html">Privacy</a> · <a href="{up}api/">Free API</a>'
            + (f' · <a href="{escape(tg)}" rel="noopener">Telegram</a>' if tg else ""))
    dr = ' dir="rtl"' if lang == "ur" else ""
    return (f'<!doctype html><html lang="{lang}"{dr}><head>{"".join(head)}</head><body>'
            f'<header><a class="logo" href="{up}index.html">{escape(NAME)}</a><nav>{navh}</nav>'
            f'<button id="theme" class="ghost" title="Dark / light" aria-label="Toggle theme">◐</button></header>'
            f'<main>{body}</main><footer><p>{foot}</p><p>Rates are indicative mid-market values for information only, '
            f'not financial advice. &copy; {datetime.date.today().year} {escape(NAME)}</p></footer>'
            f'<script>window.UP="{up}";</script><script src="{up}app.js" defer></script></body></html>')


def make_png(size):
    bg, fg = (11, 61, 145), (255, 255, 255)
    rows = []
    cx = cy = (size - 1) / 2.0
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            d = math.hypot(x - cx, y - cy) / size
            col = bg
            if d < 0.34: col = fg
            if d < 0.34 and abs(y - cy) < size * 0.06 and abs(x - cx) < size * 0.2: col = bg
            row += bytes(col)
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


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

    def rt(rs, a, b): return rs[b] / rs[a]
    def series(a, b):
        ds = [d for d in dates_all[-60:] if a in hist[d] and b in hist[d]]
        return ds, [rt(hist[d], a, b) for d in ds]

    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy(os.path.join(ASSETS, "style.css"), os.path.join(OUT, "style.css"))
    shutil.copy(os.path.join(ASSETS, "app.js"), os.path.join(OUT, "app.js"))
    sw = open(os.path.join(ASSETS, "sw.js"), encoding="utf-8").read().replace("%V%", TODAY)
    w("sw.js", sw)
    for s in (192, 512):
        with open(os.path.join(OUT, f"icon-{s}.png"), "wb") as f: f.write(make_png(s))
    w("icon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0b3d91"/><circle cx="32" cy="32" r="21" fill="#fff"/><rect x="19" y="29" width="26" height="6" fill="#0b3d91"/></svg>')
    w("manifest.json", jd({"name": NAME, "short_name": NAME, "start_url": "./", "scope": "./", "display": "standalone",
        "theme_color": "#0b3d91", "background_color": "#ffffff",
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
        json.dump(mlog[-14:], open(os.path.join(DATA, "movers.json"), "w"))
        mlog = mlog[-14:]

    # ---- pair pages
    count = 0
    for a in codes:
        for b in codes:
            if not allowed(a, b): continue
            r = rates[b] / rates[a]
            ds, vs = series(a, b)
            ins = insight(a, b, ds, vs)
            na, nb = CUR[a], CUR[b]
            chg = ""
            if len(vs) >= 2:
                p = (vs[-1] - vs[-2]) / vs[-2] * 100
                chg = f' <span class="{"up" if p >= 0 else "down"}">{p:+.2f}% vs previous day</span>'
            link_amt = (a, b) in popset
            rows = "".join(
                f'<tr><td>{(f"<a href=\"../{x}-{slug(a,b)}/\">{x:,} {a}</a>" if link_amt and x in AMT2 else f"{x:,} {a}")}</td>'
                f'<td>{money(x*r)} {b}</td></tr>' for x in AMOUNTS)
            stats = ""
            for wdw in (7, 30, 60):
                if len(vs) >= wdw:
                    seg = vs[-wdw:]
                    stats += (f"<tr><td>{wdw} days</td><td>{fmt(max(seg))}</td><td>{fmt(min(seg))}</td>"
                              f"<td>{fmt(sum(seg)/len(seg))}</td><td>{(seg[-1]-seg[0])/seg[0]*100:+.2f}%</td></tr>")
            stats_h = (f'<table><tr><th>Period</th><th>High</th><th>Low</th><th>Average</th><th>Change</th></tr>{stats}</table>'
                       if stats else "<p>History is still building up: this section fills in automatically every day.</p>")
            insh = ""
            if ins:
                insh = (f'<div class="box insight"><div class="score s{ins["pct"]//20 if ins["pct"]<100 else 4}">'
                        f'<b>{ins["pct"]}</b><small>/100</small></div><div><h2>Timing insight: {ins["label"]}</h2>'
                        f'<p>{escape(ins["text"])}</p></div></div>')
            ch = chart(ds, vs)
            others = [x for x in codes if x not in (a, b) and allowed(a, x)]
            others2 = [x for x in codes if x not in (a, b) and allowed(x, b)]
            rel1 = "".join(f'<a href="../{slug(a,x)}/">{a} to {x}</a>' for x in others[:12])
            rel2 = "".join(f'<a href="../{slug(x,b)}/">{x} to {b}</a>' for x in others2[:12])
            hubl = f'<p><a href="../{hub(a)}/">All {na} exchange rates</a></p>'
            urlnk = ""
            alts = None
            if "PKR" in (a, b) and not ({a, b} & METALS):
                urlnk = f'<p><a href="../ur/{slug(a,b)}/" hreflang="ur">اردو میں دیکھیں</a></p>'
                alts = [("en", f"{slug(a,b)}/"), ("ur", f"ur/{slug(a,b)}/")]
            tm = ""
            if len(vs) >= 3:
                tm = (f'<h3>Time machine</h3><p>What if you had converted <input id="tmamt" type="number" value="100" min="0" step="any" style="max-width:110px"> {a} '
                      f'<input id="tm" type="range" min="0" max="{len(vs)-1}" value="{min(7, len(vs)-1)}"> <b id="tmlab"></b>?</p>'
                      f'<p id="tmout"></p>')
            if a in METALS:
                nm = na.split(" (")[0]
                title = f"{nm} Price in {nb} Today – {a} to {b}"
                desc = f"1 troy ounce of {nm.lower()} = {fmt(r)} {b} today. Live {a} to {b} price, table and history."
            elif b == "PKR":
                title = f"{na} Rate in Pakistan Today – {a} to PKR"
                desc = f"1 {a} = {fmt(r)} PKR today. {na} to Pakistani Rupee converter, 7-day history, timing insight and rate alerts."
            else:
                title = f"{a} to {b} Today – {na} to {nb} Exchange Rate"
                desc = f"1 {a} = {fmt(r)} {b} today. Live {na} to {nb} converter, history chart, fee calculator and rate alerts."
            faq = [(f"What is the {a} to {b} rate today?", f"Today 1 {na} equals {fmt(r)} {nb}."),
                   (f"How much is 100 {a} in {b}?", f"100 {a} is about {money(100*r)} {b}."),
                   (f"How much is 1 {b} in {a}?", f"1 {b} is about {fmt(1/r)} {a}."),
                   ("Where do these rates come from?", "They are mid-market rates refreshed daily. Banks and money changers add their own margin, so the rate you actually get can differ.")]
            schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": t}} for q, t in faq]}
            faqh = "".join(f"<p><b>{escape(q)}</b><br>{escape(t)}</p>" for q, t in faq)
            pd = {"a": a, "b": b, "r": r, "d": ds, "v": [float(f"{v:.8g}") for v in vs]}
            body = f"""<h1>{a} to {b} – {na} to {nb}</h1>
<div class="box"><div class="rate">1 {a} = {fmt(r)} {b}</div><p>Updated {TODAY}.{chg}</p>
<p>Convert: <input id="amt" type="number" value="1" min="0" step="any"> {a} = <b id="out"></b> {b}</p>
<div class="row"><button id="fav">☆ Save pair</button><button id="share">Share</button></div></div>
{adblock()}{insh}
{('<div class="box"><h2>' + a + ' to ' + b + ' – history</h2>' + ch + '</div>') if ch else ''}
<div class="box"><h2>Smart tools</h2>
<h3>Bank / exchange fee</h3><p>Margin % <input id="fee" type="number" value="0" min="0" max="25" step="0.1" style="max-width:90px">
 &nbsp;You receive <b id="feeout"></b> {b} <small>(fee costs <span id="feecost"></span> {b})</small></p>
{tm}
<h3>Rate alert</h3><p>Tell me when 1 {a} is <select id="aldir"><option value="above">above</option><option value="below">below</option></select>
<input id="alt" type="number" step="any" placeholder="{fmt(r)}" style="max-width:130px"> {b} <button id="albtn">Set alert</button></p>
<p id="almsg"><small>Alerts work whenever this site is open or installed on your phone (menu &gt; Add to Home screen).</small></p><div id="allist"></div></div>
{affbox()}
<h2>{na} to {nb} conversion table</h2><table><tr><th>{a}</th><th>{b}</th></tr>{rows}</table>
<h2>Statistics</h2>{stats_h}
{adblock()}<h2>Frequently asked questions</h2>{faqh}
<h2>More {a} rates</h2><div class="grid">{rel1}</div><h2>More rates to {b}</h2><div class="grid">{rel2}</div>
{hubl}{urlnk}<p><a href="../widget/">Get this converter as a free widget for your website</a></p>
<script type="application/json" id="pd">{jd(pd)}</script>"""
            w(f"{slug(a,b)}/index.html", shell(title, desc, f"{slug(a,b)}/", body, alts=alts, schema=schema, has_gold=has_gold))
            urls.append(f"{SITE}/{slug(a,b)}/"); count += 1

    # ---- long-tail amount pages for popular pairs
    ac = 0
    for a, b in POPULAR:
        if a not in rates or b not in rates: continue
        r = rates[b] / rates[a]; na, nb = CUR[a], CUR[b]
        for x in AMT2:
            near = [y for y in AMT2 if y != x][:0] or [y for y in AMT2 if y != x and 0.1 <= y / x <= 10][:8]
            nrows = "".join(f'<tr><td><a href="../{y}-{slug(a,b)}/">{y:,} {a}</a></td><td>{money(y*r)} {b}</td></tr>' for y in near)
            body = f"""<h1>{x:,} {a} to {b}</h1>
<div class="box"><div class="rate">{x:,} {a} = {money(x*r)} {b}</div><p>{x:,} {na} in {nb}, rate of {TODAY}: 1 {a} = {fmt(r)} {b}.</p>
<p>Other amount: <input id="amt" type="number" value="{x}" min="0" step="any"> {a} = <b id="out"></b> {b}</p></div>
{adblock()}<h2>Nearby amounts</h2><table><tr><th>{a}</th><th>{b}</th></tr>{nrows}</table>
<p>How much is {x:,} {b} in {a}? About {money(x/r)} {a}.</p>
<p><a href="../{slug(a,b)}/">Full {a} to {b} page with chart, insight and alerts</a> · <a href="../{slug(b,a)}/">{b} to {a}</a></p>
<script type="application/json" id="pd">{jd({"a": a, "b": b, "r": r})}</script>"""
            title = f"{x:,} {a} to {b} – {x:,} {na} in {nb} Today"
            desc = f"{x:,} {a} = {money(x*r)} {b} today. Convert {x:,} {na} to {nb} at the latest exchange rate."
            w(f"{x}-{slug(a,b)}/index.html", shell(title, desc, f"{x}-{slug(a,b)}/", body, has_gold=has_gold))
            urls.append(f"{SITE}/{x}-{slug(a,b)}/"); ac += 1

    # ---- Urdu pages (PKR pairs)
    uc = 0
    for c in codes:
        if c == "PKR": continue
        for a, b in ((c, "PKR"), ("PKR", c)):
            if not allowed(a, b): continue
            r = rates[b] / rates[a]
            rows = "".join(f"<tr><td>{x:,} {a}</td><td>{money(x*r)} {b}</td></tr>" for x in AMOUNTS)
            body = f"""<h1>{a} سے {b} — آج کا ریٹ</h1>
<div class="box"><div class="rate">1 {a} = {fmt(r)} {b}</div><p>{UR[a]} کی قیمت {UR[b]} میں — تاریخ {TODAY}</p>
<p>رقم: <input id="amt" type="number" value="1" min="0" step="any"> {a} = <b id="out"></b> {b}</p></div>
{adblock()}<table><tr><th>{a}</th><th>{b}</th></tr>{rows}</table>
<p><a href="../../{slug(a,b)}/">View in English (chart, alerts, tools)</a></p>
<script type="application/json" id="pd">{jd({"a": a, "b": b, "r": r})}</script>"""
            title = f"{UR[a]} کا ریٹ آج ({a} to {b}) — {UR[b]} میں"
            desc = f"آج 1 {a} = {fmt(r)} {b}۔ {UR[a]} سے {UR[b]} کنورٹر اور ریٹ ٹیبل۔"
            w(f"ur/{slug(a,b)}/index.html", shell(title, desc, f"ur/{slug(a,b)}/", body, up="../../", lang="ur",
                alts=[("en", f"{slug(a,b)}/"), ("ur", f"ur/{slug(a,b)}/")], has_gold=has_gold))
            urls.append(f"{SITE}/ur/{slug(a,b)}/"); uc += 1

    # ---- hubs (live multi-convert)
    for a in codes:
        trs = "".join(f'<tr data-r="{rates[x]/rates[a]}"><td><a href="../{slug(a,x)}/">{x}</a> <small>{CUR[x]}</small></td><td class="v">{fmt(rates[x]/rates[a])}</td></tr>'
                      for x in codes if allowed(a, x))
        body = f"""<h1>{CUR[a]} ({a}) exchange rates</h1><p>Type an amount and see it in every currency at once.</p>
<div class="box"><input id="hamt" type="number" value="1" min="0" step="any"> {a}</div>{adblock()}
<table class="scale"><tr><th>Currency</th><th>Value</th></tr>{trs}</table>"""
        w(f"{hub(a)}/index.html", shell(f"{CUR[a]} ({a}) Exchange Rates Today", f"{CUR[a]} against {len(codes)-1} currencies: live multi-converter, updated daily.",
            f"{hub(a)}/", body, has_gold=has_gold))
        urls.append(f"{SITE}/{hub(a)}/")

    # ---- today / movers
    if movers:
        def mrow(m): return f'<tr><td><a href="../{slug(m[0],"PKR")}/">{m[0]}</a> {CUR[m[0]]}</td><td>{fmt(m[1])} PKR</td><td class="{"up" if m[2]>=0 else "down"}">{m[2]:+.2f}%</td></tr>'
        allr = "".join(mrow(m) for m in movers)
        body = (f"<h1>Currency movers today – {TODAY}</h1><p>How each currency moved against the Pakistani Rupee since yesterday.</p>{adblock()}"
                f"<h2>Biggest gainers vs PKR</h2><table><tr><th>Currency</th><th>Price</th><th>Change</th></tr>{''.join(mrow(m) for m in movers[:5])}</table>"
                f"<h2>Biggest decliners vs PKR</h2><table><tr><th>Currency</th><th>Price</th><th>Change</th></tr>{''.join(mrow(m) for m in movers[::-1][:5])}</table>"
                f"<h2>All currencies</h2><table><tr><th>Currency</th><th>Price</th><th>Change</th></tr>{allr}</table>"
                f'<p><a href="../rss.xml">RSS feed</a></p>')
    else:
        body = "<h1>Currency movers today</h1><p>Daily movers appear here once two days of data are collected.</p>"
    w("today/index.html", shell(f"Currency Movers Today – {TODAY}", "Which currencies gained or lost against the Pakistani Rupee today.", "today/", body, has_gold=has_gold))
    urls.append(f"{SITE}/today/")
    items = "".join(
        f"<item><title>Currency movers {m['date']}</title><link>{SITE}/today/</link><guid isPermaLink=\"false\">{m['date']}</guid>"
        f"<description>{escape('Up: ' + ', '.join(f'{x[0]} {x[2]:+.2f}%' for x in m['up']) + ' | Down: ' + ', '.join(f'{x[0]} {x[2]:+.2f}%' for x in m['down']))}</description></item>"
        for m in reversed(mlog))
    w("rss.xml", f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{escape(NAME)} – movers</title><link>{SITE}/</link><description>Daily currency movers vs PKR</description>{items}</channel></rss>')

    # ---- send money to Pakistan
    if "PKR" in rates:
        opts = "".join(f'<option value="{c}">{c} – {CUR[c]}</option>' for c in SENDERS if c in rates)
        trs = "".join(f'<tr><td><a href="../{slug(c,"PKR")}/">{c}</a> {CUR[c]}</td><td>{fmt(rates["PKR"]/rates[c])} PKR</td></tr>' for c in SENDERS if c in rates and c != "PKR")
        body = f"""<h1>Send money to Pakistan – today's rates and fee calculator</h1>
<p>See how many rupees your family receives. Enter your bank or app's margin to see the real amount.</p>
<div class="box"><p>Send <input id="samt" type="number" value="500" min="0" step="any" style="max-width:130px">
<select id="sfrom">{opts}</select> &nbsp; margin % <input id="sfee" type="number" value="2" min="0" max="25" step="0.1" style="max-width:80px"></p>
<p class="rate">They receive: <span id="sout"></span> PKR</p><p><small>Mid-market value: <span id="smid"></span> PKR. Margin cost: <span id="scost"></span> PKR.</small></p></div>
{affbox()}{adblock()}<h2>Today's rates to PKR</h2><table><tr><th>Currency</th><th>1 unit =</th></tr>{trs}</table>{ratestag}"""
        w("send-money-to-pakistan/index.html", shell("Send Money to Pakistan – Exchange Rates & Fee Calculator", "Compare today's rates to PKR from USD, GBP, EUR, AED, SAR and more, and calculate what your family really receives after fees.", "send-money-to-pakistan/", body, has_gold=has_gold))
        urls.append(f"{SITE}/send-money-to-pakistan/")

    # ---- gold
    if has_gold:
        gd = {c: rates[c] / rates["XAU"] for c in codes if c not in METALS}
        gcur = "".join(f'<option value="{c}"{" selected" if c=="PKR" else ""}>{c}</option>' for c in gd)
        opk = gd["PKR"]
        def line(k): return f'<tr><td>{k}K</td><td>{money(opk/31.1034768*k/24)}</td><td>{money(opk/31.1034768*k/24*11.6638038)}</td><td>{money(opk/31.1034768*k/24*10)}</td></tr>'
        body = f"""<h1>Gold rate in Pakistan today – per tola, gram and ounce</h1>
<div class="box"><p class="rate">1 troy ounce (24K) = {money(opk)} PKR</p>
<p><small>International spot price converted to PKR on {TODAY}. Local jewellers add premiums, making charges and taxes, so shop prices differ.</small></p></div>
<table><tr><th>Purity</th><th>Per gram (PKR)</th><th>Per tola (PKR)</th><th>10 grams (PKR)</th></tr>{line(24)}{line(22)}{line(21)}{line(18)}</table>{adblock()}
<div class="box"><h2>Gold value calculator</h2><p><input id="gw" type="number" value="1" min="0" step="any" style="max-width:100px">
<select id="gu"><option value="11.6638038">tola</option><option value="1">gram</option><option value="31.1034768">ounce</option></select>
<select id="gk"><option value="24">24K</option><option value="22" selected>22K</option><option value="21">21K</option><option value="18">18K</option></select>
<select id="gc">{gcur}</select> making charges % <input id="gm" type="number" value="0" min="0" max="50" step="0.5" style="max-width:80px"></p>
<p class="rate"><span id="gout"></span></p></div>
<script type="application/json" id="gd">{jd(gd)}</script>"""
        w("gold-rate-in-pakistan/index.html", shell("Gold Rate in Pakistan Today – Per Tola, Gram & Ounce", "Today's gold price in Pakistan per tola, gram and ounce for 24K, 22K, 21K and 18K, with a gold value calculator.", "gold-rate-in-pakistan/", body, has_gold=True))
        urls.append(f"{SITE}/gold-rate-in-pakistan/")

    # ---- API + widget
    w("api/latest.json", jd({"base": "USD", "date": TODAY, "rates": rjson["rates"]}))
    for a in codes:
        w(f"api/{a.lower()}.json", jd({"base": a, "date": TODAY, "rates": {x: rates[x] / rates[a] for x in codes if x != a}}))
    body = f"""<h1>Free currency API</h1><p>Free, no key, no limits, updated daily, CORS enabled. Please link back to {escape(NAME)}.</p>
<div class="box"><p><code>{SITE}/api/latest.json</code> (base USD)<br><code>{SITE}/api/pkr.json</code> (any base: usd, eur, gbp, aed ...)</p>
<pre>fetch("{SITE}/api/usd.json").then(r=&gt;r.json()).then(d=&gt;console.log(d.rates.PKR))</pre></div>
<p>Currencies: {", ".join(codes)}</p>"""
    w("api/index.html", shell("Free Currency Exchange Rate API", "Free daily currency exchange rate JSON API with no key.", "api/", body, has_gold=has_gold))
    urls.append(f"{SITE}/api/")
    opts = "".join(f'<option value="{c}">{c}</option>' for c in codes if c not in METALS)
    body = f"""<h1>Free currency converter widget</h1><p>Add a live converter to your website. Choose a pair, copy the code, paste it into your page.</p>
<div class="box"><p>From <select id="wf">{opts}</select> To <select id="wt">{opts}</select></p>
<textarea id="wcode" rows="4" style="width:100%" readonly></textarea><p>Preview:</p><iframe id="wprev" width="320" height="170" style="border:0"></iframe></div>
<script type="application/json" id="wsite">{jd(SITE)}</script>"""
    w("widget/index.html", shell("Free Currency Converter Widget for Your Website", "Embed a free live currency converter on your website with one line of code.", "widget/", body, has_gold=has_gold))
    urls.append(f"{SITE}/widget/")
    w("embed.html", f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<style>body{{margin:0;font:15px system-ui,sans-serif;padding:10px;background:#fff;color:#1c2330}}input,select{{font-size:15px;padding:5px;max-width:100%}}b{{color:#0b3d91;font-size:18px}}a{{font-size:12px;color:#667}}</style></head><body>
<div><input id="ea" type="number" value="1" min="0" step="any" style="width:90px"> <select id="ef"></select></div>
<div style="margin:8px 0"><b id="eo"></b> <select id="et"></select></div>
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
    pop = "".join(f'<a href="{slug(a,b)}/">{a} to {b}</a>' for a, b in POPULAR if a in rates and b in rates)
    hubs = "".join(f'<a href="{hub(a)}/">{a} – {CUR[a]}</a>' for a in codes)
    mv = ""
    if movers:
        mv = ('<div class="box"><h2>Today vs Pakistani Rupee</h2><div class="grid">' +
              "".join(f'<a href="{slug(m[0],"PKR")}/">{m[0]} <span class="{"up" if m[2]>=0 else "down"}">{m[2]:+.2f}%</span></a>' for m in movers[:3] + movers[-3:]) +
              '</div><p><a href="today/">See all movers</a></p></div>')
    tools = ('<div class="grid"><a href="send-money-to-pakistan/">Send money to Pakistan</a>' +
             ('<a href="gold-rate-in-pakistan/">Gold rate in Pakistan</a>' if has_gold else "") +
             '<a href="today/">Today\'s movers</a><a href="widget/">Free widget</a><a href="api/">Free API</a></div>')
    ex = "".join(f'<button class="chip" data-q="{q}">{q}</button>' for q in ["500 usd to pkr", "dirham to rupee", "1000 riyal in pkr", "5k pounds in rupees", "gold"])
    body = f"""<h1>{escape(NAME)} – Smart Currency Converter & Daily Exchange Rates</h1>
<div class="box hero"><p>Type or speak, in plain words:</p>
<div class="row"><input id="cmd" type="text" placeholder="e.g. 500 dollar in rupees" autocomplete="off" style="flex:1;max-width:none"><button id="mic" title="Speak">🎤</button></div>
<div id="cmdout" class="cmdout"></div><div class="grid">{ex}</div></div>
<div class="box"><h2>Converter</h2><p><input id="bigamt" type="number" value="100" min="0" step="any" style="max-width:120px">
<select id="bigfrom"></select> <button id="bigswap" class="ghost">⇄</button> <select id="bigto"></select></p>
<p class="rate" id="bigout"></p><p><a id="biglink" href="#">Open full page for this pair</a></p></div>
<div id="favs"></div><div id="recent"></div>{mv}{adblock()}
<h2>Tools</h2>{tools}<h2>Popular conversions</h2><div class="grid">{pop}</div><h2>All currencies</h2><div class="grid">{hubs}</div>{ratestag}"""
    sch = {"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": SITE + "/"}
    w("index.html", shell(f"{NAME} – Currency Converter & Daily Exchange Rates", "Smart currency converter with daily rates, history charts, rate alerts, gold and remittance tools for USD, PKR, AED, SAR, GBP, EUR and more.", "", body, up="", schema=sch, has_gold=has_gold))

    mail = escape(CFG.get("contact_email", ""))
    w("about.html", shell("About", "About this site", "about.html", f"<h1>About {escape(NAME)}</h1><p>{escape(NAME)} publishes free, automatically updated currency exchange rates, history, converters and tools. Rates are indicative only. Contact: {mail}</p>", up=""))
    w("privacy.html", shell("Privacy Policy", "Privacy policy", "privacy.html",
        "<h1>Privacy Policy</h1><p>This site stores your saved pairs, alerts and theme only in your own browser (local storage) and does not send them to us. "
        "Third-party vendors, including Google, use cookies to serve ads based on prior visits; you can opt out at Google Ads Settings. "
        f"Rates are for information only and are not financial advice.</p><p>Contact: {mail}</p>", up=""))
    w("404.html", shell("Page not found", "Page not found", "404.html", f'<h1>Page not found</h1><p><a href="{SITE}/">Go to the home page</a></p>', up=SITE + "/", noindex=True))
    urls += [f"{SITE}/about.html", f"{SITE}/privacy.html"]
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls)
    w("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')

    # ---- files for the announce job
    if not SAMPLE_MODE:
        open(os.path.join(DATA, "urls.txt"), "w").write("\n".join(urls))
        lines = [f"{NAME} – {TODAY}"]
        for a, b in [("USD", "PKR"), ("GBP", "PKR"), ("EUR", "PKR"), ("AED", "PKR"), ("SAR", "PKR")]:
            if a in rates and b in rates:
                ds, vs = series(a, b)
                ch = f" ({(vs[-1]-vs[-2])/vs[-2]*100:+.2f}%)" if len(vs) > 1 else ""
                lines.append(f"{a}/PKR {fmt(rates[b]/rates[a])}{ch}")
        if movers: lines.append(f"Top gainer vs PKR: {movers[0][0]} {movers[0][2]:+.2f}%")
        lines.append(SITE + "/")
        json.dump({"text": "\n".join(lines)}, open(os.path.join(DATA, "summary.json"), "w"))
    print(f"done: {count} pair pages, {ac} amount pages, {uc} urdu pages, {len(codes)} hubs, {len(urls)} urls, gold={has_gold}")


if __name__ == "__main__":
    main()
