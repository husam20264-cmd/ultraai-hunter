import json

def load_ads_from_json(path):
    try:
        with open(path, 'r') as f: return json.load(f)
    except: return []

def analyze_competitor_ads(product_name, country, ads):
    count = len(ads)
    score = 100 - (count * 10)
    return {
        "market_saturation": "early" if count < 5 else "saturated",
        "supply_signal_score": max(score, 10),
        "active_ads_count": count
    }
