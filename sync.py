"""Collect public CPP event listings directly from the endpoint used by CPP_Search."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data"
OUT.mkdir(exist_ok=True)
API = os.getenv("CPP_API_URL", "https://www.allcpp.cn/allcpp/event/eventMainListV2.do")
KEYWORDS = ["杭州", "上海", "南京", "苏州", "宁波", "无锡", "嘉兴", "绍兴", "常州", "温州", "金华", "湖州", "南通", "ONLY", "TRPG"]
MAX_PAGES = int(os.getenv("CPP_MAX_PAGES", "8"))
now = datetime.now(timezone.utc).isoformat()
errors, events, counts = {}, {}, {}

def fetch(keyword, page):
    params = {"time": 8, "sort": 1, "keyword": keyword, "pageNo": page, "pageSize": 10}
    url = API + ("&" if "?" in API else "?") + urlencode(params)
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; cpp-info-bridge/1.1)",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://cp.allcpp.cn/",
        "Origin": "https://cp.allcpp.cn",
        "errorWrap": "json",
    })
    with urlopen(req, timeout=25) as response:
        body = json.load(response)
    result = body.get("result") if isinstance(body, dict) else None
    if not isinstance(result, dict) or not isinstance(result.get("list"), list):
        raise ValueError("CPP response missing result.list")
    return result

def fmt_time(value):
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, timezone.utc).astimezone(
                __import__("zoneinfo").ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OverflowError):
        pass
    return str(value or "")

def normalize(item):
    eid = item.get("id")
    if not eid:
        return None
    return {
        "id": eid,
        "name": item.get("name", ""),
        "tag": item.get("tag", ""),
        "location": " ".join(str(item.get(k) or "") for k in ("provName", "cityName", "areaName")).strip(),
        "address": item.get("enterAddress", ""),
        "url": "https://www.allcpp.cn/allcpp/event/event.do?event=" + str(eid),
        "type": item.get("type", item.get("evmtype", "")),
        "wannaGoCount": item.get("wannaGoCount", 0),
        "circleCount": item.get("circleCount", 0),
        "doujinshiCount": item.get("doujinshiCount", 0),
        "time": fmt_time(item.get("enterTime") or item.get("startTime")),
        "end_time": fmt_time(item.get("endTime")),
        "enabled": item.get("enabled"),
        "isOnline": item.get("isOnline", 0),
    }

for keyword in KEYWORDS:
    try:
        first = fetch(keyword, 1)
        total = int(first.get("total") or 0)
        pages = min(MAX_PAGES, max(1, (total + 9) // 10))
        records = first["list"]
        for page in range(2, pages + 1):
            time.sleep(0.4)
            records += fetch(keyword, page)["list"]
        counts[keyword] = {"total_reported": total, "fetched": len(records), "truncated": total > pages * 10}
        for raw in records:
            if isinstance(raw, dict):
                item = normalize(raw)
                if item:
                    events[str(item["id"])] = item
        time.sleep(0.5)
    except Exception as exc:
        errors[keyword] = str(exc)[:250]

success = len(KEYWORDS) - len(errors)
status = {
    "updated_at": now,
    "collector_status": "ok" if success == len(KEYWORDS) else ("partial" if success else "failed"),
    "source": "CPP official eventMainListV2 endpoint (unofficial access)",
    "api_url": API,
    "queried_keywords": KEYWORDS,
    "failed_keywords": list(errors),
    "warnings": errors,
    "keyword_counts": counts,
    "event_count": len(events),
}
(OUT / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if success:
    payload = {"updated_at": now, "source": "CPP", "events": sorted(events.values(), key=lambda x: x["time"] or "9999")}
    (OUT / "latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(status, ensure_ascii=False))
if not success:
    raise SystemExit("No CPP queries succeeded; see data/status.json")
