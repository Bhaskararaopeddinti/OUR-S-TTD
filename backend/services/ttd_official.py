"""Read only publicly displayed TTD updates. No booking or private systems are accessed."""
import re
import time
from urllib.request import Request, urlopen

OFFICIAL_URL = "https://www.tirumala.org/"
_cache: tuple[float, dict] | None = None

def public_status() -> dict:
    global _cache
    if _cache and time.time() - _cache[0] < 300:
        return _cache[1]
    result = {
        "source": OFFICIAL_URL,
        "source_name": "TTD official public website",
        "verified": True,
        "wait_minutes": None,
        "crowd_density": "Not published by TTD",
        "people_count": None,
        "message": "TTD does not publish a public live queue wait-time feed. This app will show it only after authorized API access.",
        "slot": None,
        "balance_tickets": None,
    }
    try:
        request = Request(OFFICIAL_URL, headers={"User-Agent": "OURS-TTD-pilgrim-guide/1.0"})
        text = urlopen(request, timeout=12).read().decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        slot = re.search(r"Running Slot:\s*([^B]+?)\s*Balance tickets", text, re.I)
        balance = re.search(r"Balance tickets for\s*([^:]+):\s*([\d,]+)", text, re.I)
        if slot: result["slot"] = slot.group(1).strip()
        if balance: result["balance_tickets"] = {"date": balance.group(1).strip(), "count": int(balance.group(2).replace(",", ""))}
    except Exception:
        result["message"] = "Official TTD public status could not be reached right now. Please use the official website directly."
    _cache = (time.time(), result)
    return result
