import subprocess
import sys
from pathlib import Path
import json

STEPS = [
    ("1. Discovery", "duck_product_aggregator.py", 120),  # دقيقتين
    ("2. Price Scanner", "price_scout.py", 180),          # 3 دقائق (أعطيناه وقت أطول قليلاً لأنه يفتح مواقع)
    ("3. Profit Ranker", "profit_ranker.py", 30),
    ("4. Name Purifier", "product_purifier.py", 30),
    ("5. Ad Creative", "ad_creative_generator.py", 30),
    ("6. Image Downloader", "image_scout.py", 60),
    ("7. Supplier Scout", "supplier_scout.py", 90)
]

OPTIONAL_STEPS = [
    ("8. Viral Loop Engine (Optional)", "viral_loop_engine.py", 30)
]

def run():
    print("=" * 60)
    print("🚀 [UltraAI] Starting Full Product Hunter Pipeline...")
    print("=" * 60)
    
    for step_name, script, timeout in STEPS:
        print(f"\n▶️  Running: {step_name} ({script}) | Timeout: {timeout}s")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                [sys.executable, script],
                timeout=timeout 
            )
            
            if result.returncode != 0:
                print(f"⚠️ Step {step_name} failed. Continuing to next step...")
                
        except subprocess.TimeoutExpired:
            print(f"⏳ TIMEOUT: {step_name} exceeded {timeout} seconds. Skipping to next step...")
        except Exception as e:
            print(f"❌ ERROR in {step_name}: {e}. Skipping...")
    
    # تشغيل الخطوات الاختيارية
    for step_name, script, timeout in OPTIONAL_STEPS:
        print(f"\n▶️  Running Optional: {step_name} ({script})")
        print("-" * 40)
        try:
            subprocess.run([sys.executable, script], timeout=timeout)
        except Exception:
            pass

    print("\n" + "=" * 60)
    print("🏆 [UltraAI] Pipeline Completed! 🏆")
    print("=" * 60)
    
    # قراءة البيانات النهائية
    supplier_file = Path("supplier_options.json")
    viral_file = Path("viral_strategy.json")
    
    if supplier_file.exists():
        suppliers_data = json.loads(supplier_file.read_text(encoding="utf-8"))
        print("\n🎯 Ready to Launch Products:\n")
        for sup in suppliers_data:
            local_suppliers = sup.get('local_suppliers_jo', [])
            if local_suppliers:
                print(f"🟢 {sup['product_name_ar']} | Sell: {sup['suggested_selling_price_jod']} JOD")
                print(f"   📦 Where to buy: {local_suppliers[0].get('title', 'N/A')}")
                if viral_file.exists():
                    print(f"   🦠 Viral Loop: Ready in viral_strategy.json\n")
                else:
                    print()

if __name__ == "__main__":
    run()
