import json
import time
import random
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup

QUERIES = [
    "buy car accessories Jordan",
    "buy kitchen gadgets Jordan",
    "buy phone accessories Jordan",
    "buy baby products Jordan",
    "buy travel accessories Jordan",
    "buy cleaning tools Jordan",
    "شراء اكسسوارات سيارة الأردن",
    "شراء منتجات مطبخ الأردن"
]

PRODUCT_WORDS = [
    "organizer", "holder", "stand", "cushion", "support", "sprayer",
    "lamp", "roller", "brush", "cleaner", "massager", "blender",
    "humidifier", "bag", "cover", "case", "charger", "stroller",
    "منظم", "حامل", "مطبخ", "سيارة", "اكسسوارات", "شنطة", "فرشاة",
    "منظف", "أطفال", "تجميل", "هدايا", "موبايل", "رياضة"
]

# Words that indicate a SHOPPING link (filters out blogs/articles)
COMMERCIAL_WORDS = [
    "buy", "shop", "price", "cart", "store", "product", "deal", "order",
    "تسوق", "شراء", "سعر", "منتج", "متجر", "عروض", "سلة"
]

BAD_WORDS = [
    "news", "jobs", "job", "wiki", "wikipedia", "salary", "blog", "tips", "guide",
    "أخبار", "وظائف", "ويكيبيديا", "نصائح", "مدونة"
]

# Using a Desktop Browser User-Agent to bypass 403 blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def clean_duck_url(href):
    if not href:
        return ""

    if href.startswith("//"):
        href = "https:" + href

    if href.startswith("/"):
        href = "https://duckduckgo.com" + href

    # Extract the actual URL from DuckDuckGo's redirect parameter (uddg)
    if "uddg=" in href:
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])

    return href

def score_text(text, href):
    low = str(text or "").lower()
    href_low = str(href or "").lower()
    combined = low + " " + href_low
    
    score = 0

    # Must look like a commercial product page
    if any(w in combined for w in COMMERCIAL_WORDS):
        score += 30
    
    if any(w.lower() in combined for w in PRODUCT_WORDS):
        score += 30

    # Strong boost for Jordanian local stores
    if any(w in combined for w in ["jordan", "amman", ".jo", "الأردن", "عمان", "توصيل", "delivery", "سعر"]):
        score += 35

    # Penalize articles and bad words
    if any(w.lower() in combined for w in BAD_WORDS):
        score -= 50

    return max(0, min(score, 100))

def clean_name(title):
    title = str(title or "").strip()
    junk = [
        "|", " - ", "–", "—", "Amazon", "Facebook", "TikTok",
        "Jordan", "الأردن", "Online", "Buy", "Shop", "Best", "Top"
    ]
    for j in junk:
        title = title.replace(j, " ")
    return " ".join(title.split())[:80]

def search_duck_lite(query):
    url = "https://lite.duckduckgo.com/lite/"
    params = {"q": query}
    
    # Adding a session cookie helps bypass 403 Forbidden blocks
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.set("kl", "wt-wt") 

    for attempt in range(3):
        try:
            res = session.get(url, params=params, timeout=20)
            print(f"🔎 {query} | HTTP {res.status_code} | attempt {attempt + 1}")

            if res.status_code == 429:
                wait_time = 25 + random.uniform(5, 15)
                print(f"   🚫 Rate limited. Cooling down {round(wait_time, 1)}s")
                time.sleep(wait_time)
                return []

            if res.status_code == 403:
                wait_time = 15 + random.uniform(5, 10)
                print(f"   🛑 Forbidden 403. Retrying in {round(wait_time, 1)}s")
                time.sleep(wait_time)
                continue

            if res.status_code == 202:
                wait_time = (2 ** attempt) + random.uniform(3, 6)
                print(f"   ⏳ Status 202. Retrying in {round(wait_time, 1)}s")
                time.sleep(wait_time)
                continue

            if res.status_code != 200:
                wait_time = 2 + random.uniform(1, 3)
                print(f"   ⚠ HTTP {res.status_code}. Retrying in {round(wait_time, 1)}s")
                time.sleep(wait_time)
                continue

            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.find_all("a")
            results = []

            for a in links:
                title = a.get_text(" ", strip=True)
                href = clean_duck_url(a.get("href", ""))

                if not title or len(title) < 8:
                    continue

                if "duckduckgo" in title.lower() or "duckduckgo" in href.lower():
                    continue

                score = score_text(title, href)

                # Minimum score of 60 to ensure it's a real commercial product
                if score >= 60:
                    results.append({
                        "source": "DuckDuckGo_Lite",
                        "market": "Jordan",
                        "seed_query": query,
                        "offered_product": clean_name(title),
                        "raw_title": title,
                        "ad_preview_link": href,
                        "scout_score": score,
                        "status": "Discovered"
                    })

                if len(results) >= 5:
                    break

            return results

        except Exception as e:
            wait_time = (2 ** attempt) + random.uniform(1, 3)
            print(f"   ❌ Attempt {attempt + 1} failed: {e}. Retrying in {round(wait_time, 1)}s")
            time.sleep(wait_time)

    return []

def run():
    all_items = []

    for q in QUERIES:
        all_items.extend(search_duck_lite(q))
        # Increased sleep to avoid rate limits
        time.sleep(random.uniform(4, 7))

    unique = {}
    for item in all_items:
        key = item["offered_product"].lower()
        if key not in unique or item["scout_score"] > unique[key]["scout_score"]:
            unique[key] = item

    final = sorted(unique.values(), key=lambda x: x["scout_score"], reverse=True)

    Path("product_candidates_structured.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    Path("product_candidates.json").write_text(
        json.dumps([x["offered_product"] for x in final[:15]], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n--- Saved {len(final)} products ---")

if __name__ == "__main__":
    run()
