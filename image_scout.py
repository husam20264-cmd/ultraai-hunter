import json
import time
import random
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

INPUT_FILE = Path("ad_creatives.json")
OUTPUT_FILE = Path("final_products.json")
IMAGE_DIR = Path("ad_images")

IMAGE_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def search_and_download_image(query, filename):
    # البحث في صور Bing (أسهل في الـ Scraping من DuckDuckGo)
    search_url = f"https://www.bing.com/images/search?q={quote_plus(query + ' product white background')}&first=1"
    
    try:
        res = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # البحث عن أكبر تاج فيه رابط الصورة (m=img) في Bing
        img_tag = soup.find("a", class_="iusc")
        
        if img_tag and img_tag.get("m"):
            # رابط الصورة مخزن كـ JSON داخل خاصية m
            m_data = json.loads(img_tag["m"])
            img_url = m_data.get("murl") # murl = Main URL للصورة الأصلية
            
            if img_url:
                # تحميل الصورة وحفظها محلياً
                img_res = requests.get(img_url, headers=HEADERS, timeout=15, stream=True)
                if img_res.status_code == 200:
                    filepath = IMAGE_DIR / filename
                    with open(filepath, "wb") as f:
                        for chunk in img_res.iter_content(1024):
                            f.write(chunk)
                    return img_url, str(filepath)
                    
        # Plan B: البحث عن أي تاج img عادي
        img_tag2 = soup.find("img", class_="mimg")
        if img_tag2 and img_tag2.get("src"):
            src = img_tag2["src"]
            if src.startswith("http"):
                img_res = requests.get(src, headers=HEADERS, timeout=15, stream=True)
                if img_res.status_code == 200:
                    filepath = IMAGE_DIR / filename
                    with open(filepath, "wb") as f:
                        for chunk in img_res.iter_content(1024):
                            f.write(chunk)
                    return src, str(filepath)

    except Exception as e:
        print(f"   ⚠️ Image search failed: {e}")
    
    return None, None

def main():
    if not INPUT_FILE.exists():
        print("❌ Run ad_creative_generator.py first!")
        return

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    final_products = []

    print("🖼️ Fetching product images from Bing...\n")

    for i, item in enumerate(data):
        product_name = item["suggested_product_ar"]
        cat = item["category"]
        price = item["suggested_price_jod"]
        
        search_terms = {
            "Kitchen Essentials": "spice rack rotating 360 product",
            "Kitchen Tools & Gadgets": "electric vegetable chopper product",
            "Car Accessories": "car backseat organizer product"
        }
        
        query = search_terms.get(cat, product_name)
        filename = f"product_{i+1}.jpg"
        
        print(f"🔎 Searching & downloading: {product_name} ({query})")
        
        img_url, local_path = search_and_download_image(query, filename)
        
        if img_url:
            print(f"   ✅ Downloaded to: {local_path}")
        else:
            print(f"   ❌ No image found.")
        
        final_products.append({
            "category": cat,
            "product_name_ar": product_name,
            "ad_copy_ar": item["ad_copy_ar"],
            "price_jod": price,
            "image_url": img_url or "NO_IMAGE_FOUND",
            "local_image_path": local_path or "NO_LOCAL_IMAGE",
            "status": "🟢 Ready for Ad" if img_url else "🔴 Needs Manual Image"
        })
        
        time.sleep(random.uniform(2, 4))

    OUTPUT_FILE.write_text(
        json.dumps(final_products, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n🏆 Saved {len(final_products)} final products to final_products.json")
    print(f"📂 Images saved in folder: {IMAGE_DIR}/")
    print("=" * 60)
    for p in final_products:
        print(f"{p['status']} | {p['product_name_ar']} | {p['price_jod']} JOD")

if __name__ == "__main__":
    main()
