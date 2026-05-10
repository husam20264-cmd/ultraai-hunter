import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from pytrends.request import TrendReq

# --- الإعدادات ---
SCOUT_RESULTS = Path("scout_results.json")
RATE_LIMIT_FILE = Path("google_trends_rate_limit.json")

SEED_KEYWORDS = ["neck pain", "car accessories", "home organization"]
COUNTRY_GEO = {"Jordan": "JO", "Saudi Arabia": "SA", "UAE": "AE"}

def safe_int(val, default=0):
    try: return int(val)
    except: return default

def dedupe_by_keyword(items):
    seen = set()
    unique = []
    for i in items:
        k = i['keyword'].lower().strip()
        if k not in seen:
            seen.add(k)
            unique.append(i)
    return unique

# --- إدارة الحظر الذكية (v2.3) ---
def is_google_trends_paused():
    if not RATE_LIMIT_FILE.exists(): return False
    try:
        data = json.loads(RATE_LIMIT_FILE.read_text())
        pause_until = datetime.fromisoformat(data.get("pause_until"))
        # استخدام التوقيت العالمي الحديث
        return datetime.now(timezone.utc) < pause_until
    except: return False

def pause_google_trends(minutes=45):
    pause_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    RATE_LIMIT_FILE.write_text(json.dumps({
        "pause_until": pause_until.isoformat(),
        "reason": "429 Rate Limit Detected"
    }, indent=2))
    print(f"\n⛔ [SYSTEM] Google Trends paused until {pause_until.isoformat()} UTC")

def is_rate_limit_error(error):
    text = str(error).lower()
    return any(x in text for x in ["429", "too many requests", "scraper", "limit"])

# --- محرك البحث المطور ---
def discover_google_trends(country="Jordan", limit_per_seed=10):
    # 1. التحقق من الحظر المسبق
    if is_google_trends_paused():
        print("⏳ [SKIP] Google Trends is in recovery mode. Skipping...")
        return []

    # 2. تنظيف ملف الحظر القديم لبدء محاولة فريش مع الـ IP الجديد
    if RATE_LIMIT_FILE.exists():
        try:
            RATE_LIMIT_FILE.unlink()
            print("🧼 [CLEAN] Old rate-limit file removed for a fresh start.")
        except: pass

    geo = COUNTRY_GEO.get(country, "JO")
    discovered = []
    
    print(f"\n--- 🔎 Starting Google Trends Scan ({geo}) ---")

    for seed in SEED_KEYWORDS:
        print(f"🔎 Scanning: {seed}")
        
        # فاصل زمني عشوائي (نبض بشري)
        wait = random.uniform(12, 25)
        print(f"⏱ Waiting {round(wait, 1)}s...")
        time.sleep(wait)

        try:
            # استخدام timeouts أطول لتناسب جودة الإنترنت في Termux
            pytrends = TrendReq(hl="en-US", tz=180, timeout=(20, 45))
            pytrends.build_payload(kw_list=[seed], geo=geo, timeframe="now 7-d")
            related = pytrends.related_queries()
            
            if seed not in related: continue
            
            data = related[seed]
            for section in ["rising", "top"]:
                df = data.get(section)
                if df is None or df.empty: continue
                
                for _, row in df.head(limit_per_seed).iterrows():
                    query = str(row.get("query", "")).strip()
                    value = safe_int(row.get("value", 0))
                    if query:
                        discovered.append({
                            "source": "google_trends",
                            "seed": seed,
                            "keyword": query,
                            "trend_value": value,
                            "country": country,
                        })
        except Exception as e:
            print(f"💥 [ERROR] {seed}: {e}")
            if is_rate_limit_error(e):
                print("🚨 Rate limit (429) hit! Triggering safety pause.")
                pause_google_trends(minutes=60)
                break 
            continue
            
    return dedupe_by_keyword(discovered)

if __name__ == "__main__":
    print(f"🚀 [START] Product Scout v2.3 | UTC: {datetime.now(timezone.utc)}")
    results = discover_google_trends(country="Jordan")
    
    if results:
        print(f"\n✅ [SUCCESS] Found {len(results)} opportunities.")
        SCOUT_RESULTS.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("\n⚠️ [FINISH] No new results. Change IP and try again.")
