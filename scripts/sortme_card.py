import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# твой id из /profile/5076
HANDLE_OR_ID = "5076"

OUT_PATH = "assets/sortme.svg"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

ENDPOINTS = [
    # варианты, потому что у Sort-Me часть API живёт на api.sort-me.org
    "https://api.sort-me.org/api/users/getByHandle?handle={h}",
    "https://api.sort-me.org/users/getByHandle?handle={h}",
    "https://api.sort-me.org/api/users/getById?id={h}",
    "https://api.sort-me.org/users/getById?id={h}",

    "https://sort-me.org/api/users/getByHandle?handle={h}",
    "https://sort-me.org/users/getByHandle?handle={h}",
    "https://sort-me.org/api/users/getById?id={h}",
    "https://sort-me.org/users/getById?id={h}",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (GitHub Actions; sortme-card)",
    "Accept": "application/json,text/plain,*/*",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch(url: str) -> tuple[int, str]:
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
    # иногда даже в HTML (или в "не-JSON") встречается нужный кусок
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

    # иногда "Solved 72" текстом
    if total is None:
        m_solved = re.search(r"Solved[^0-9]{0,30}(\d+)", body, re.I)
        if m_solved:
            total = int(m_solved.group(1))

    return total, diffs

def get_user_data():
    quoted = urllib.parse.quote(HANDLE_OR_ID)
    last_head = ""
    for tpl in ENDPOINTS:
        url = tpl.format(h=quoted)
        try:
            status, body = fetch(url)
        except Exception as e:
            print(f"[Sort-Me] GET {url} -> ERROR: {e}")
            continue

        head = body[:200].replace("\n", " ")
        print(f"[Sort-Me] GET {url} -> status={status} head={head!r}")

        js = try_parse_json(body)
        if js is not None:
            print(f"[Sort-Me] ✅ JSON from: {url}")
            return js

        # если не JSON, попробуем вытащить хотя бы total/diffs
        total, diffs = try_extract_from_text(body)
        if total is not None or diffs is not None:
            print(f"[Sort-Me] ✅ extracted from non-JSON: {url} (total={total}, diffs={diffs})")
            # вернём “псевдо-json” в ожидаемом формате
            return {
                "handle": HANDLE_OR_ID,
                "regal": {
                    "statistics": {
                        "total": total or 0,
                        "difficulties": diffs or [0, 0, 0, 0, 0],
                    }
                }
            }

        last_head = head

    print(f"[Sort-Me] ❌ Could not get stats. Last head: {last_head!r}")
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

  <a href="{profile_link}" target="_blank" rel="noopener noreferrer">
    <text x="420" y="146" fill="#93c5fd" font-size="11" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
      open profile →
    </text>
  </a>
</svg>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"[Sort-Me] FINAL total={total}, diffs={diffs}, rank={rank_text}")
print(f"Wrote {OUT_PATH}")
