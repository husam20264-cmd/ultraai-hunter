import json
import os
from datetime import datetime
from pathlib import Path
from trend_alert import analyze_keyword
from comment_analyzer import analyze_comments
from competitor_ad_tracker import analyze_competitor_ads
from triple_match_orchestrator import final_triple_match_decision
from ad_creative_generator import generate_ad_creative_pack
from pdf_report_generator import generate_investment_report

HISTORY_FILE = Path("history.json")

def save_analysis_history(product_name, country, score, decision, recommendation):
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
        except: history = []

    # توحيد الاسم (Normalization): إزالة المسافات الزائدة وتنسيق الحروف
    clean_name = product_name.strip().title()

    history.append({
        "product_name": clean_name,
        "country": country,
        "score": score,
        "decision": decision,
        "recommendation": recommendation,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    
    HISTORY_FILE.write_text(json.dumps(history[-50:], ensure_ascii=False, indent=2), encoding='utf-8')

def run_full_scan(product_name, country, category):
    try:
        with open('comments.json', 'r', encoding='utf-8') as f:
            all_comments = json.load(f)
            product_comments = all_comments.get(product_name, [])
    except: product_comments = []

    try:
        with open('ads.json', 'r', encoding='utf-8') as f:
            all_ads = json.load(f)
    except: all_ads = []

    demand_res = analyze_keyword(product_name, country)
    attention_res = analyze_comments(product_name, country, product_comments)
    competition_res = analyze_competitor_ads(product_name, country, all_ads)

    decision_res = final_triple_match_decision(
        demand_res['baseline_growth_pct'],
        attention_res['attention_score'],
        competition_res['supply_signal_score'],
        competition_res['market_saturation']
    )

    save_analysis_history(
        product_name, 
        country, 
        decision_res['confidence'], 
        decision_res['decision'], 
        decision_res['recommendation']
    )

    pdf_path = generate_investment_report(product_name, country, demand_res, attention_res, competition_res, decision_res)

    return {
        "triple_match_result": decision_res,
        "pdf_path": pdf_path
    }
