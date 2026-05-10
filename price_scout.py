import json
import re
import time
import random
from pathlib import Path

import requests
from bs4 import BeautifulSoup

INPUT_FILE = Path("product_candidates_structured.json")
OUTPUT_FILE = Path("product_price_scan.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

PRICE_PATTERNS = [
    r"(\d{2,}(?:\.\d{1,2})?)\s*(?:JOD|JD|دينار)",
    r"(?:JOD|JD|دينار)\s*(\d{2,}(?:\.\d{1,2})?)",
    r"(\d{2,}(?:\.\d{1,2})?)\s*د\.أ",
]

def extract_price(text):
    text = text.replace(",", "")
    
    for pattern in PRICE_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                price = float(match.group(1))
                if 2 <= price <= 1500:
                    return price
            except:
                pass

    soup = BeautifulSoup(text, "html.parser")
    
    # Shopify / Modern stores meta tags
    for meta in soup.find_all("meta", attrs={"property": re.compile(r"product:price:amount")}):
        content = meta.get("content", "")
        try:
            price = float(content)
            if 2 <= price <= 1500:
                return price
        except:
            pass

    # JSON-LD structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                offers = data.get("offers", {})
                price_str = offers.get("price", "")
                if price_str:
                    price = float(price_str)
                    if 2 <= price <= 1500:
                        return price
        except:
            pass

    # OpenSooq specific span class
    for span in soup.find_all("span", class_=re.compile(r"price", re.I)):
        ptext = span.get_text(strip=True)
        for pattern in PRICE_PATTERNS:
            m = re.search(pattern, ptext, re.I)
            if m:
                try:
                    price = float(m.group(1))
                    if 2 <= price <= 1500:
                        return price
                except:
                    pass

    return None

def scan_url(item):
    url = item.get("ad_preview_link", "")
    if not url or not url.startswith("http"):
        return {**item, "price_status": "invalid_url", "detected_price": None}

    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        html = res.text
        price = extract_price(html)

        return {
            **item,
            "price_status": "found" if price else "not_found",
            "detected_price": price,
            "http_status": res.status_code
        }

    except Exception as e:
        return {**item, "price_status": "error", "detected_price": None, "error": str(e)}

def main():
    if not INPUT_FILE.exists():
        print("product_candidates_structured.json not found")
        return

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    results = []

    for item in data[:15]:
        print("Scanning:", item.get("offered_product"))
        result = scan_url(item)
        results.append(result)
        time.sleep(random.uniform(2, 5))

    OUTPUT_FILE.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\nSaved:", OUTPUT_FILE)
    print("-" * 50)
    
    found_count = 0
    for r in results:
        if r.get("detected_price"):
            found_count += 1
            print(f"\u2728 {r.get('detected_price')} JOD | {r.get('offered_product')}")
        else:
            print(f"\u274c None JOD | {r.get('offered_product')}")
            
    print(f"\n\U0001f3c6 Found prices for {found_count} / {len(results)} products.")

if __name__ == "__main__":
    main()
