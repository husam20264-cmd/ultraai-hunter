import json
import time
import random
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

INPUT_FILE = Path("ad_creatives.json")
OUTPUT_FILE = Path("supplier_options.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

# قاموس البحث: اسم المنتج -> كلمات البحث المحلية + كلمات البحث الخارجية
SEARCH_MAP = {
    "Kitchen Essentials": {
        "local_queries": ["حامل توابل الأردن", "منظم مطبخ توصيل عمان"],
        "global_queries": ["spice rack supplier turkey", "kitchen organizer dropship uae"]
    },
    "Kitchen Tools & Gadgets": {
        "local_queries": ["مفرمة خضار الأردن", "مفرمة مطبخ كهربائية عمان"],
        "global_queries": ["electric vegetable chopper wholesale", "kitchen chopper supplier dubai"]
    },
    "Car Accessories": {
        "local_queries": ["منظم سيارة الأردن", "اكسسوارات سيارة توصيل عمان"],
        "global_queries": ["car backseat organizer supplier", "car accessories dropship uae"]
    }
}

def search_suppliers(query):
    url = "https://lite.duckduckgo.com/lite/"
    params = {"q": query}
    
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []
            
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.find_all("a")
        
        results = []
        for a in links:
            title = a.get_text(" ", strip=True)
            href = a.get("href", "")
            
            if not title or len(title) < 8 or "duckduckgo" in title.lower():
                continue
                
            # استبعاد الروابط غير المفيدة (أخبار، ويكيبيديا)
            bad = ["wiki", "news", "facebook", "instagram", "youtube", "pinterest"]
            if any(b in href.lower() or b in title.lower() for b in bad):
                continue
                
            results.append({
                "title": title[:80],
                "url": href
            })
            
            if len(results) >= 3: # نكتفي بأول 3 نتائج واعدة
                break
                
        return results
        
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        return []

def main():
    if not INPUT_FILE.exists():
        print("❌ Run ad_creative_generator.py first!")
        return

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    all_suppliers = []

    print("🏭 Searching for Alternative Suppliers (No AliExpress)...\n")

    for item in data:
        cat = item["category"]
        product = item["suggested_product_ar"]
        price = item["suggested_price_jod"]
        
        if cat not in SEARCH_MAP:
            continue
            
        queries_data = SEARCH_MAP[cat]
        
        print(f"🔍 Product: {product} ({cat})")
        
        local_results = []
        global_results = []
        
        # 1. البحث المحلي (الأردن/عمان)
        for q in queries_data["local_queries"]:
            print(f"   🇯🇴 Local search: {q}")
            local_results.extend(search_suppliers(q))
            time.sleep(random.uniform(2, 3))
            
        # 2. البحث الخارجي (تركيا/ الإمارات/ جملة)
        for q in queries_data["global_queries"]:
            print(f"   🌍 Global search: {q}")
            global_results.extend(search_suppliers(q))
            time.sleep(random.uniform(2, 3))
            
        all_suppliers.append({
            "product_name_ar": product,
            "category": cat,
            "suggested_selling_price_jod": price,
            "local_suppliers_jo": local_results[:3],
            "global_suppliers": global_results[:3]
        })
        
        print(f"   ✅ Found {len(local_results[:3])} local, {len(global_results[:3])} global\n")

    OUTPUT_FILE.write_text(
        json.dumps(all_suppliers, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print("=" * 60)
    print("🏭 Supplier Options Summary:")
    print("=" * 60)
    for s in all_suppliers:
        print(f"\n📦 {s['product_name_ar']} (Sell at: {s['suggested_selling_price_jod']} JOD)")
        print(f"   🇯🇴 Local Suppliers:")
        if not s['local_suppliers_jo']:
            print("      - No direct local found (Try local Facebook groups)")
        for l in s['local_suppliers_jo']:
            print(f"      - {l['title']}")
        print(f"   🌍 Global Suppliers:")
        if not s['global_suppliers']:
            print("      - No global found")
        for g in s['global_suppliers']:
            print(f"      - {g['title']}")

if __name__ == "__main__":
    main()
