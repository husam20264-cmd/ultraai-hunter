import random

def analyze_keyword(keyword, country, alert_threshold_pct=200.0):
    growth = random.randint(150, 450)
    return {
        "status": "breakout" if growth > alert_threshold_pct else "stable",
        "baseline_growth_pct": growth,
        "current_value": random.randint(70, 100),
        "baseline_value": random.randint(20, 30)
    }
