import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HANDLE_OR_ID = "5076"

OUT_PATH = "assets/sortme.svg"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

ENDPOINTS = [
    "https://api.sort-me.org/api/users/getByHandle?handle={h}",
    "https://api.sort-me.org/users/getByHandle?handle={h}",
    "https://api.sort-me.org/api/users/getById?id={h}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (GitHub Actions)",
    "Accept": "application/json,text/plain,*/*",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def try_parse_json(body: str):
    s = body.lstrip()
    if s.startswith("{"):
        try:
            return json.loads(body)
        except:
            return None
    return None

def get_data():
    quoted = urllib.parse.quote(HANDLE_OR_ID)
    for tpl in ENDPOINTS:
        try:
            body = fetch(tpl.format(h=quoted))
            js = try_parse_json(body)
            if js:
                return js
        except:
            continue
    return {}

data = get_data() or {}

regal = data.get("regal") or {}
stats = regal.get("statistics") or {}
rank_record = regal.get("rank_record") or {}

total = stats.get("total", 0)
diffs = (stats.get("difficulties") or [0,0,0,0,0])[:5]

easy, medium, hard, vhard, imp = diffs
rank = rank_record.get("rank", "—")

updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def bar(x, max_val, color):
    width = 360
    percent = 0 if max_val == 0 else x / max_val
    fill = percent * width
    return f'''
      <rect x="30" y="{bar.y}" width="{width}" height="10" rx="5" fill="#24283b"/>
      <rect x="30" y="{bar.y}" width="{fill}" height="10" rx="5" fill="{color}"/>
    '''

svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="260">

  <defs>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1a1b27"/>
      <stop offset="100%" stop-color="#16161e"/>
    </linearGradient>
  </defs>

  <rect width="600" height="260" rx="20" fill="url(#grad)"/>

  <text x="30" y="45" fill="#bb9af7" font-size="22" font-family="Segoe UI" font-weight="600">
    Sort-Me Dashboard
  </text>

  <text x="30" y="75" fill="#7aa2f7" font-size="14" font-family="Segoe UI">
    Rank: #{rank}
  </text>

  <text x="30" y="105" fill="#c0caf5" font-size="16" font-family="Segoe UI">
    Solved:
    <tspan fill="#9ece6a" font-weight="700"> {total}</tspan>
  </text>
"""

max_val = max(total, 1)

bar.y = 130
svg += bar(easy, max_val, "#9ece6a")
svg += f'<text x="400" y="138" fill="#c0caf5" font-size="12">Easy {easy}</text>'

bar.y = 150
svg += bar(medium, max_val, "#e0af68")
svg += f'<text x="400" y="158" fill="#c0caf5" font-size="12">Medium {medium}</text>'

bar.y = 170
svg += bar(hard, max_val, "#f7768e")
svg += f'<text x="400" y="178" fill="#c0caf5" font-size="12">Hard {hard}</text>'

bar.y = 190
svg += bar(vhard, max_val, "#bb9af7")
svg += f'<text x="400" y="198" fill="#c0caf5" font-size="12">VHard {vhard}</text>'

bar.y = 210
svg += bar(imp, max_val, "#7dcfff")
svg += f'<text x="400" y="218" fill="#c0caf5" font-size="12">Imp {imp}</text>'

svg += f"""
  <text x="380" y="245" fill="#565f89" font-size="11">
    updated {updated}
  </text>

</svg>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(svg)

print("Wrote Tokyo Night styled Sort-Me card")
