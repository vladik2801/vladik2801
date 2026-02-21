import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Твой профиль Sort-Me
HANDLE_OR_ID = "5076"

OUT_PATH = "assets/sortme.svg"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

ENDPOINTS = [
    "https://api.sort-me.org/api/users/getByHandle?handle={h}",
    "https://api.sort-me.org/users/getByHandle?handle={h}",
    "https://api.sort-me.org/api/users/getById?id={h}",
    "https://api.sort-me.org/users/getById?id={h}",
    "https://sort-me.org/api/users/getByHandle?handle={h}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (GitHub Actions; sortme-card)",
    "Accept": "application/json,text/plain,*/*",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        status = getattr(r, "status", 200)
        body = r.read().decode("utf-8", errors="replace")
        return status, body

def try_parse_json(body: str):
    s = body.lstrip()
    if s.startswith("{") or s.startswith("["):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return None

def try_extract_from_text(body: str):
    m_total = re.search(r'"total"\s*:\s*(\d+)', body)
    total = int(m_total.group(1)) if m_total else None

    m_diff = re.search(r'"difficulties"\s*:\s*\[(.*?)\]', body, re.S)
    diffs = None
    if m_diff:
        nums = re.findall(r'\d+', m_diff.group(1))
        if nums:
            diffs = list(map(int, nums[:5]))
            diffs += [0] * (5 - len(diffs))
            diffs = diffs[:5]

    return total, diffs

def get_user_data():
    quoted = urllib.parse.quote(HANDLE_OR_ID)

    for tpl in ENDPOINTS:
        url = tpl.format(h=quoted)
        try:
            status, body = fetch(url)
        except Exception:
            continue

        js = try_parse_json(body)
        if js:
            return js

        total, diffs = try_extract_from_text(body)
        if total is not None:
            return {
                "handle": HANDLE_OR_ID,
                "regal": {
                    "statistics": {
                        "total": total,
                        "difficulties": diffs or [0, 0, 0, 0, 0],
                    }
                }
            }

    return {}

data = get_user_data() or {}

handle = data.get("handle", HANDLE_OR_ID)
name = data.get("name", "")

regal = data.get("regal") or {}
stats = regal.get("statistics") or {}
rank_record = regal.get("rank_record") or {}

total = stats.get("total", 0)
diffs = stats.get("difficulties") or [0, 0, 0, 0, 0]
diffs = (diffs + [0, 0, 0, 0, 0])[:5]

easy, medium, hard, vhard, imp = diffs

rank = rank_record.get("rank", None)
rank_text = f"#{rank}" if isinstance(rank, int) else "—"

updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
profile_link = f"https://sort-me.org/profile/{HANDLE_OR_ID}"

# === TOKYO NIGHT SVG ===

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="200" viewBox="0 0 540 200">

  <rect width="540" height="200" rx="18" fill="#1a1b27"/>

  <text x="30" y="45" fill="#bb9af7" font-size="22" font-family="Segoe UI, sans-serif" font-weight="600">
    Sort-Me Stats
  </text>

  <text x="30" y="75" fill="#7aa2f7" font-size="14" font-family="Segoe UI, sans-serif">
    {handle}{(" — " + name) if name else ""}
  </text>

  <text x="30" y="115" fill="#c0caf5" font-size="16" font-family="Segoe UI, sans-serif">
    Solved:
    <tspan fill="#9ece6a" font-weight="700"> {total}</tspan>
  </text>

  <text x="30" y="140" fill="#c0caf5" font-size="13" font-family="Segoe UI, sans-serif">
    Easy <tspan fill="#9ece6a">{easy}</tspan>
    · Medium <tspan fill="#e0af68">{medium}</tspan>
    · Hard <tspan fill="#f7768e">{hard}</tspan>
  </text>

  <text x="30" y="160" fill="#c0caf5" font-size="13" font-family="Segoe UI, sans-serif">
    Very Hard <tspan fill="#f7768e">{vhard}</tspan>
    · Impossible <tspan fill="#bb9af7">{imp}</tspan>
  </text>

  <text x="380" y="185" fill="#565f89" font-size="11" font-family="Segoe UI, sans-serif">
    updated {updated}
  </text>

</svg>"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"[Sort-Me] FINAL total={total}, diffs={diffs}, rank={rank_text}")
print(f"Wrote {OUT_PATH}")
