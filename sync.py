import json, os, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
API = os.environ.get("CPP_API_URL", "https://api.mihoyo.su/manzhan.php")
KEYWORDS = ["杭州","上海","南京","苏州","宁波","无锡","嘉兴","绍兴","常州","温州","金华","湖州","南通","ONLY","TRPG"]
now = datetime.now(timezone.utc).isoformat()
items, errors = {}, {}
for word in KEYWORDS:
    try:
        url = API + ("&" if "?" in API else "?") + urlencode({"msg":word,"debug":"raw"})
        req = Request(url, headers={"User-Agent":"CPP-Bridge/1.0","Accept":"application/json"})
        with urlopen(req, timeout=18) as response:
            payload = json.load(response)
        if not isinstance(payload, dict) or payload.get("code") != 200 or not isinstance(payload.get("data"), list):
            raise ValueError("Unexpected API response")
        for entry in payload["data"]:
            if not isinstance(entry, dict): continue
            key = str(entry.get("id") or entry.get("url") or "")
            if key: items.setdefault(key, entry)
        time.sleep(1.5)
    except Exception as exc:
        errors[word] = str(exc)[:240]
records = sorted(items.values(), key=lambda x: str(x.get("time") or "9999"))
status = {"updated_at":now,"collector_status":"ok" if not errors else ("partial" if len(errors)<len(KEYWORDS) else "failed"),"source":"CPP_Search third-party API","api_url":API,"queried_keywords":KEYWORDS,"failed_keywords":list(errors),"warnings":errors,"event_count":len(records)}
(OUT/"status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if len(errors)<len(KEYWORDS):
    (OUT/"latest.json").write_text(json.dumps({"updated_at":now,"source":"CPP_Search","events":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(status,ensure_ascii=False))
