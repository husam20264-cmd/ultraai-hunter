from pathlib import Path
import json
import requests

BASE = "http://127.0.0.1:8000"

ENDPOINTS = [
    "/",
    "/hunter",
    "/api/check-status",
    "/api/top-products",
    "/api/product-hunter",
]

FILES = [
    "final_products.json",
    "supplier_options.json",
    "product_winners_clean.json",
    "ad_creatives.json",
    "viral_strategy.json",
]

def check_endpoint(path):
    try:
        r = requests.get(BASE + path, timeout=5)
        status = "OK" if r.status_code == 200 else "FAIL"
        print(f"{status:4} | {r.status_code} | {path}")
    except Exception as e:
        print(f"ERR  | ---- | {path} | {e}")

def check_json_file(file):
    p = Path(file)
    if not p.exists():
        print(f"MISS | {file}")
        return

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        count = len(data) if isinstance(data, list) else len(data.keys())
        print(f"OK   | {file} | items: {count}")
    except Exception as e:
        print(f"BAD  | {file} | {e}")

def check_images():
    p = Path("ad_images")
    if not p.exists():
        print("MISS | ad_images folder")
        return

    imgs = list(p.glob("*.jpg")) + list(p.glob("*.png")) + list(p.glob("*.webp"))
    print(f"OK   | ad_images | images: {len(imgs)}")
    for img in imgs[:5]:
        print(f"     - {img}")

def check_product_images_from_json():
    p = Path("final_products.json")
    if not p.exists():
        return

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except:
        return

    print("\nProduct image paths:")
    for item in data:
        name = item.get("product_name_ar")
        path = item.get("local_image_path")
        exists = Path(path).exists() if path and path != "NO_LOCAL_IMAGE" else False
        print(f"{'OK' if exists else 'MISS'} | {name} | {path}")

def main():
    print("\n=== API / Pages Test ===")
    for e in ENDPOINTS:
        check_endpoint(e)

    print("\n=== JSON Files Test ===")
    for f in FILES:
        check_json_file(f)

    print("\n=== Images Folder Test ===")
    check_images()

    check_product_images_from_json()

    print("\nDone.")

if __name__ == "__main__":
    main()
