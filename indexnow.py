import json, urllib.request

cfg = json.load(open("config.json", encoding="utf-8"))
site = cfg["site_url"].rstrip("/")
key = cfg.get("indexnow_key", "")
if not key:
    print("no indexnow key - skipping")
    raise SystemExit(0)
urls = [u.strip() for u in open("data/urls.txt", encoding="utf-8") if u.strip()]
host = site.split("//", 1)[1].split("/")[0]
for i in range(0, len(urls), 9000):
    body = json.dumps({"host": host, "key": key, "keyLocation": f"{site}/{key}.txt",
                       "urlList": urls[i:i + 9000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/IndexNow", body,
                                 {"Content-Type": "application/json; charset=utf-8"})
    try:
        print("indexnow status", urllib.request.urlopen(req, timeout=60).status)
    except Exception as e:
        print("indexnow failed (not critical):", e)
