def analyze_comments(product_name, country, comments, source="manual"):
    intent_words = ["بكم", "سعر", "توصيل", "طلب", "وين", "price", "order"]
    count = sum(1 for c in comments if any(w in c.lower() for w in intent_words))
    ratio = (count / len(comments)) * 100 if comments else 0
    return {
        "status": "high_intent" if ratio > 50 else "low_intent",
        "attention_score": int(ratio),
        "purchase_intent_ratio_pct": int(ratio),
        "sample_purchase_intent_comments": comments[:3]
    }
