import json
import os
import urllib.request
from datetime import datetime, timezone

USER_ID_OR_HANDLE = "5076"  
API_URL = f"https://sort-me.org/api/users/getByHandle?handle={USER_ID_OR_HANDLE}"

OUT_PATH = "assets/sortme.svg"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

def get_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (GitHub Actions; sortme-card)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

data = get_json(API_URL)

handle = data.get("handle", "unknown")
name = data.get("name", "")
regal = data.get("regal") or {}
rank = (regal.get("rank_record") or {}).get("rank", None)
stats = regal.get("statistics") or {}
total = stats.get("total", 0)
diffs = stats.get("difficulties") or [0, 0, 0, 0, 0]

easy, medium, hard, vhard, imp = (diffs + [0, 0, 0, 0, 0])[:5]

updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
rank_text = f"#{rank}" if isinstance(rank, int) else "—"

# Простая SVG-карточка в стиле "dark"
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="520" height="160" viewBox="0 0 520 160" role="img" aria-label="Sort-Me stats">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#0b1220"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
  </defs>

  <rect x="0" y="0" width="520" height="160" rx="16" fill="url(#bg)" />

  <text x="22" y="38" fill="#e5e7eb" font-size="18" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Sort-Me
  </text>
  <text x="22" y="64" fill="#a5b4fc" font-size="14" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    {handle}{(" — " + name) if name else ""}
  </text>

  <text x="22" y="98" fill="#e5e7eb" font-size="14" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Rank: <tspan fill="#f9fafb" font-weight="700">{rank_text}</tspan>
  </text>
  <text x="150" y="98" fill="#e5e7eb" font-size="14" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Solved: <tspan fill="#f9fafb" font-weight="700">{total}</tspan>
  </text>

  <text x="22" y="124" fill="#94a3b8" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Easy {easy} · Medium {medium} · Hard {hard} · VHard {vhard} · Imp {imp}
  </text>

  <text x="22" y="146" fill="#64748b" font-size="11" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Updated: {updated}
  </text>

  <a href="https://sort-me.org/profile/{USER_ID_OR_HANDLE}" target="_blank" rel="noopener noreferrer">
    <text x="420" y="146" fill="#93c5fd" font-size="11" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
      open profile →
    </text>
  </a>
</svg>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"Wrote {OUT_PATH}")
