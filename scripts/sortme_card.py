import json
import os
import re
import urllib.request
from datetime import datetime, timezone

PROFILE_ID = "5076"
PROFILE_URL = f"https://sort-me.org/profile/{PROFILE_ID}"

OUT_PATH = "assets/sortme.svg"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (GitHub Actions; sortme-card)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        status = getattr(r, "status", 200)
        body = r.read().decode("utf-8", errors="replace")
        return status, body

def extract_total_and_diffs(html: str):
    """
    Пытаемся достать статистику из:
    1) встраиваемого JSON (preloaded state / hydration)
    2) простого поиска по ключам "total" / "difficulties"
    3) фолбэк по тексту "Solved" (если на странице есть цифра)
    """
    # 1) Иногда данные лежат внутри JSON в script-тегах
    # Например: <script id="__NEXT_DATA__" type="application/json">...</script>
    m_next = re.search(r'id="__NEXT_DATA__"\s+type="application/json"\s*>\s*(\{.*?\})\s*</script>', html, re.S)
    if m_next:
        try:
            data = json.loads(m_next.group(1))
            # универсального пути нет, поэтому ещё раз “грубо” вытащим из JSON-строки:
            s = json.dumps(data)
            total = first_int_after_key(s, "total")
            diffs = array_after_key(s, "difficulties", 5)
            return total, diffs
        except Exception:
            pass

    # 2) Грубый, но часто 100% рабочий вариант: ищем "total": число
    total = first_int_after_key(html, "total")
    diffs = array_after_key(html, "difficulties", 5)

    # 3) Если нет ключей, попробуем вытащить из текста “Solved”
    if total is None:
        m_solved = re.search(r"Solved[^0-9]{0,20}(\d+)", html, re.I)
        if m_solved:
            total = int(m_solved.group(1))

    return total, diffs

def first_int_after_key(text: str, key: str):
    # ищем "key": 123
    m = re.search(rf'"{re.escape(key)}"\s*:\s*(\d+)', text)
    return int(m.group(1)) if m else None

def array_after_key(text: str, key: str, n: int):
    # ищем "key": [1,2,3,4,5]
    m = re.search(rf'"{re.escape(key)}"\s*:\s*\[(.*?)\]', text, re.S)
    if not m:
        return None
    nums = re.findall(r'\d+', m.group(1))
    if not nums:
        return None
    arr = list(map(int, nums[:n]))
    if len(arr) < n:
        arr += [0] * (n - len(arr))
    return arr

status, html = fetch(PROFILE_URL)
print(f"[Sort-Me] HTML GET {PROFILE_URL} -> status={status}")
print(f"[Sort-Me] html_head={html[:200]!r}")

total, diffs = extract_total_and_diffs(html)

# минимальные фолбэки, чтобы карточка всегда рисовалась
if total is None:
    total = 0
if not diffs:
    diffs = [0, 0, 0, 0, 0]

easy, medium, hard, vhard, imp = diffs[:5]

updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

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
    {PROFILE_ID}
  </text>

  <text x="22" y="98" fill="#e5e7eb" font-size="14" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Solved: <tspan fill="#f9fafb" font-weight="700">{total}</tspan>
  </text>

  <text x="22" y="124" fill="#94a3b8" font-size="12" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Easy {easy} · Medium {medium} · Hard {hard} · VHard {vhard} · Imp {imp}
  </text>

  <text x="22" y="146" fill="#64748b" font-size="11" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
    Updated: {updated}
  </text>

  <a href="{PROFILE_URL}" target="_blank" rel="noopener noreferrer">
    <text x="420" y="146" fill="#93c5fd" font-size="11" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto">
      open profile →
    </text>
  </a>
</svg>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"[Sort-Me] Parsed total={total}, diffs={diffs}")
print(f"Wrote {OUT_PATH}")
