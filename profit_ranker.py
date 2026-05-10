import json
from pathlib import Path

PRICE_FILE = Path("product_price_scan.json")
OUTPUT_FILE = Path("product_hunter.json")

# Estimated AliExpress wholesale cost (in JOD) for typical categories
COST_ESTIMATES = {
    "kitchen": 4,
    "car": 5,
    "phone": 3,
    "accessories": 3,
    "cleaning": 4,
    "baby": 5,
    "beauty": 4,
    "organizer": 3,
    "home": 5,
    "default": 6
}

def estimate_cost(product_name):
    low = product_name.lower()
    for key, cost in COST_ESTIMATES.items():
        if key in low:
            return cost
    return COST_ESTIMATES["default"]

def main():
    if not PRICE_FILE.exists():
        print("❌ Run price_scout.py first!")
        return

    data = json.loads(PRICE_FILE.read_text(encoding="utf-8"))
    winners = []

    for item in data:
        if item.get("price_status") != "found" or not item.get("detected_price"):
            continue

        local_price = item["detected_price"]
        product_name = item.get("offered_product", "Unknown")
        cost = estimate_cost(product_name)

        # Ensure local price makes sense (ignore massive outliers like 999 JOD for accessories)
        if local_price > 150:
            continue

        profit = round(local_price - cost, 2)
        margin = round((profit / local_price) * 100, 1) if local_price > 0 else 0

        # Only include products with at least 40% margin
        if margin >= 40:
            decision = "LAUNCH 🚀" if margin >= 70 else "PROMISING 👀" if margin >= 50 else "WATCHLIST ⏳"
            
            winners.append({
                "product_name": product_name,
                "local_price_jod": local_price,
                "estimated_cost_jod": cost,
                "estimated_profit_jod": profit,
                "margin_percent": margin,
                "decision": decision,
                "source_link": item.get("ad_preview_link", "")
            })

    # Sort by highest margin
    winners.sort(key=lambda x: x["margin_percent"], reverse=True)

    OUTPUT_FILE.write_text(
        json.dumps(winners, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n🏆 Found {len(winners)} profitable products!\n")
    print(f"{'Margin':<10} | {'Profit':<10} | {'Price':<10} | Product")
    print("-" * 70)
    
    for w in winners:
        print(f"{w['margin_percent']}%      | {w['estimated_profit_jod']} JOD   | {w['local_price_jod']} JOD   | {w['product_name']}")

if __name__ == "__main__":
    main()
