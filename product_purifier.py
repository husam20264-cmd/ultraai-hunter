import json
from pathlib import Path
from collections import defaultdict

INPUT_FILE = Path("product_price_scan.json")
OUTPUT_FILE = Path("product_winners_clean.json")

# قائمة بالكلمات اللي تدل على متجر أو صفحة (بنحذفها)
JUNK_WORDS = [
    "store", "shop", "official site", "website", "online", "sale", "buy",
    "best", "top", "affordable", "wholesale", "number one", "everything you need",
    "in", "for", "at", "now", "and", "with", "from",
    "متجر", "تسوق", "أونلاين", "للبيع", "أفضل", "موقع", "رسمي", "خرما", "موتور ويلز"
]

# قاموس المنتجات الحقيقية
PRODUCT_DICTIONARY = {
    "kitchen tools": "Kitchen Tools & Gadgets",
    "kitchen gadgets": "Kitchen Gadgets",
    "kitchen essentials": "Kitchen Essentials",
    "utensils": "Kitchen Utensils",
    "cookware": "Cookware & Home Appliances",
    "car accessories": "Car Accessories",
    "car phone holder": "Car Phone Holder",
    "car mount": "Car Phone Mount",
    "phone accessories": "Phone Accessories",
    "phone case": "Phone Case",
    "mobile accessories": "Mobile Accessories",
    "baby products": "Baby Products",
    "stroller": "Baby Stroller",
    "cleaning tools": "Cleaning Tools",
    "beauty tools": "Beauty Tools",
    "home organization": "Home Organizers",
    "organizer": "Home Organizers",
    # قاموس عربي
    "مستلزمات المطبخ": "Kitchen Essentials",
    "اكسسوارات المطبخ": "Kitchen Gadgets",
    "اكسسوارات سيارة": "Car Accessories",
    "قطع سيارات": "Car Parts",
    "أدوات مطبخ": "Kitchen Utensils",
}

# المتاجر العامة اللي بنستبعدها تماماً
BANNED_STORES = [
    "al-aryan", "actionmobile", "bci tech", "orange mobile",
    "autobeeb", "labeb", "iService"
]

# حدود الأسعار المقبولة للمنتجات الاندفاعية (JOD)
MIN_PRICE = 5
MAX_PRICE = 25

def purify_name(raw_title):
    if not raw_title:
        return "Unknown Product"
    
    low = str(raw_title).lower()
    
    # 1. استبعاد المتاجر العامة
    for banned in BANNED_STORES:
        if banned in low:
            return "BANNED"

    # 2. البحث في قاموس المنتجات (عربي وانجليزي)
    for key, clean_name in PRODUCT_DICTIONARY.items():
        if key in low:
            return clean_name

    # 3. تنظيف الكلمات الزائدة يدوياً
    clean = raw_title
    for junk in JUNK_WORDS:
        clean = clean.replace(junk.title(), "")
        clean = clean.replace(junk.capitalize(), "")
        clean = clean.replace(junk, "")
    
    # إزالة المسافات المتعددة
    clean = " ".join(clean.split())
    
    if len(clean) < 3:
        return raw_title.strip()[:40]
        
    return clean.strip()[:50]

def main():
    if not INPUT_FILE.exists():
        print("❌ Run price_scout.py first!")
        return

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    
    # تخزين مؤقت لدمج المنتجات المتشابهة وجمع أسعارها
    products_data = defaultdict(list)

    print("🧹 Purifying product names & filtering prices...\n")

    for item in data:
        if item.get("price_status") != "found" or not item.get("detected_price"):
            continue

        raw_title = item.get("offered_product", "Unknown")
        local_price = item["detected_price"]
        
        pure_name = purify_name(raw_title)

        # تخطي المتاجر المستبعدة
        if pure_name == "BANNED":
            print(f"   🚫 Banned Store: {raw_title} ({local_price} JOD)")
            continue

        # تخطي الأسعار الشاذة (أقل من 5 أو أعلى من 25 دينار)
        if local_price < MIN_PRICE or local_price > MAX_PRICE:
            print(f"   ⚠️ Price out of range ({local_price} JOD): {raw_title}")
            continue

        products_data[pure_name].append({
            "price": local_price,
            "link": item.get("ad_preview_link", "")
        })

    # بناء القائمة النهائية مع حساب متوسط السعر
    winners = []
    for name, details in products_data.items():
        prices = [d["price"] for d in details]
        avg_price = round(sum(prices) / len(prices), 2)
        
        winners.append({
            "clean_product_name": name,
            "avg_price_jod": avg_price,
            "min_price_jod": min(prices),
            "max_price_jod": max(prices),
            "competitor_count": len(prices),
            "source_links": [d["link"] for d in details],
            "market": "Jordan"
        })

    # ترتيب حسب عدد المنافسين (أكبر إشارة طلب)
    winners.sort(key=lambda x: x["competitor_count"], reverse=True)

    OUTPUT_FILE.write_text(
        json.dumps(winners, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n✅ Saved {len(winners)} clean impulse-buy products to product_winners_clean.json\n")
    print(f"{'Product Name':<30} | {'Avg Price':<10} | {'Range':<15} | Competitors")
    print("-" * 85)
    for w in winners:
        print(f"{w['clean_product_name']:<30} | {w['avg_price_jod']} JOD   | {w['min_price_jod']}-{w['max_price_jod']} JOD     | {w['competitor_count']} stores")

if __name__ == "__main__":
    main()
