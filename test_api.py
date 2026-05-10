from pytrends.request import TrendReq
import pandas as pd

def quick_test():
    print("⏳ Testing Google Trends connection...")
    try:
        pytrends = TrendReq(hl='en-US', tz=180, timeout=(10,20))
        # فحص بسيط جداً على كلمة واحدة
        pytrends.build_payload(kw_list=['Jordan'], geo='JO', timeframe='now 1-d')
        df = pytrends.interest_over_time()
        if not df.empty:
            print("✅ Connection Successful! Data received.")
        else:
            print("⚠️ Connected but no data found (Normal for low volume).")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    quick_test()
