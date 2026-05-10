def final_triple_match_decision(demand_growth_pct, attention_score, supply_signal_score, market_saturation):
    # تحويل القيم لضمان العمليات الحسابية
    demand = float(demand_growth_pct or 0)
    attention = float(attention_score or 0)
    supply = float(supply_signal_score or 0)

    # حساب النتيجة الموزونة
    weighted_score = ((demand / 5) * 0.3) + (attention * 0.5) + (supply * 0.2)
    confidence = max(min(int(weighted_score), 98), 10)
    
    # القواعد الجديدة بناءً على اقتراحك
    if confidence >= 85:
        decision = "STRONG LAUNCH — إطلاق قوي"
        action = "اطلق الحملة فوراً بميزانية كاملة 🚀"
    elif confidence >= 70:
        decision = "FAST TEST — اختبار سريع"
        action = "ابدأ باختبار سريع ومحتوى متنوع ⚡"
    elif confidence >= 55:
        decision = "PROMISING — واعد"
        action = "اختبره بمحتوى قصير وميزانية صغيرة 📉"
    elif confidence >= 40:
        decision = "WATCHLIST — قائمة المراقبة"
        action = "راقب السوق، الطلب غير كافٍ حالياً ⏳"
    else:
        decision = "AVOID — تجنب الإطلاق"
        action = "المخاطرة عالية، ابحث عن منتج آخر 🛑"
        
    return {
        "decision": decision,
        "confidence": confidence,
        "recommendation": action
    }
