import json
import re
from pathlib import Path

FILES = [
    "product_candidates_structured.json",
    "duck_scout_results.json",
    "opensooq_scout_results.json",
    "product_candidates.json"
]

MIN_SCORE = 60

PRODUCT_MAP = [
    ("neck support", "Neck Support Brace"),
    ("مشدات", "Neck Support Brace"),
    ("tempur", "Tempur Neck Pillow"),
    ("neck collar", "Neck Collar Device Pillow"),
    ("air traction", "Air Traction Neck Brace"),
    ("neck pain relief", "Neck Pain Relief Pillow"),
    ("neck massager", "Neck Massager"),
    ("massage chair", "Massage Chair"),
    ("scalp massager", "Scalp Massager"),
    ("massage & recovery", "Massage Recovery Device"),
    ("manual massagers", "Manual Massager"),
    ("electric massagers", "Electric Massager"),
]

def clean_product_name(text):
    t = str(text or "").strip()
    low = t.lower()

    for key, clean in PRODUCT_MAP:
        if key in low:
            return clean

    # إزالة أسماء المواقع والزوائد
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"\bAmazon\.com\b|\bOfficial Site\b|\bjordan-corsets\.com\b", "", t, flags=re.I)
    t = re.sub(r"\|.*$", "", t)
    t = re.sub(r"\s*-\s*.*$", "", t)
    t = re.sub(r"\.\.\.$", "", t)
    t = " ".join(t.split())

    return t[:60]

winners = []

def add_winner(name, score=0):
    name = clean_product_name(name)
    if len(name) >= 3:
        winners.append({"name": name, "score": score})

for file in FILES:
    path = Path(file)
    if not path.exists():
        continue

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue

        for item in data:
            if isinstance(item, str):
                add_winner(item, 0)

            elif isinstance(item, dict):
                score = item.get("scout_score") or item.get("local_signal_score") or item.get("score") or 0
                try:
                    score = int(score)
                except:
                    score = 0

                if score >= MIN_SCORE:
                    name = (
                        item.get("offered_product")
                        or item.get("candidate")
                        or item.get("product_name")
                        or item.get("title")
                    )
                    add_winner(name, score)

    except Exception:
        continue

unique = {}
for item in winners:
    key = item["name"].lower()
    if key not in unique or item["score"] > unique[key]["score"]:
        unique[key] = item

final = sorted(unique.values(), key=lambda x: x["score"], reverse=True)

if not final:
    print("NO_WINNERS")
else:
    for item in final[:10]:
        print(item["name"])
