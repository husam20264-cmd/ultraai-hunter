import json
from pathlib import Path

HISTORY_FILE = Path("history.json")

if not HISTORY_FILE.exists():
    print("NO_WINNER")
    raise SystemExit

history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

if not history:
    print("NO_WINNER")
    raise SystemExit

# آخر حالة لكل منتج
latest = {}
for item in history:
    name = str(item.get("product_name", "")).strip().lower()
    if name:
        latest[name] = item

# الرابح = أعلى سكور من آخر الحالات فقط
winner = max(latest.values(), key=lambda x: x.get("score", 0))

print(winner.get("product_name"))
