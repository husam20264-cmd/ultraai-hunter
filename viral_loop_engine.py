import json
from pathlib import Path

INPUT_FILE = Path("final_products.json")
OUTPUT_FILE = Path("viral_strategy.json")

def main():
    if not INPUT_FILE.exists():
        print("❌ Run ultraai_pipeline.py first!")
        return

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    viral_data = []

    print("🦠 Generating Viral Loop Strategy (Zero Ad Spend)...\n")

    for item in data:
        if "Needs" in item.get("status", ""):
            continue

        cat = item.get("category", "")
        product_name = item["product_name_ar"]
        price = item["price_jod"]
        
        # السيناريو المفصل بحسب طلبك
        scripts = []
        if "توابل" in product_name or cat == "Kitchen Essentials":
            scripts.append({
                "hook_type": "داء/دواء - فوضى مقابل ترتيب (10s Video)",
                "visual_timeline": {
                    "0-2s": "دولاب بهارات مكركب، أكياس ومرطبانات فوق بعض 💥",
                    "2-5s": "تحط البهارات على الحامل 📦",
                    "5-8s": "تلف الحامل 360 درجة ببطء ✨",
                    "8-10s": "لقطة نهائية مرتبة 🌟"
                },
                "on_screen_text": {
                    "0-2s": "كل مرة بدك بهار بصير هيك؟ 😅",
                    "2-5s": "رتبناها بثواني",
                    "5-8s": "كلهم قدامك بلفة وحدة",
                    "8-10s": "مناسب للمطابخ الصغيرة"
                },
                "organic_caption": "أخيراً خلصت من فوضى البهارات بالمطبخ 😅🌶️\nكلهم صاروا قدامي بلفة وحدة.\n\nولما يسألوك:\nآه متوفر، سعره 10 دنانير والتوصيل داخل عمان.\nبدك أحجرلك واحد؟",
                "in_box_card": "شكراً لطلبك 🌸\nصوّر حامل التوابل بعد ما ترتبه في مطبخك وابعث لنا الصورة/الفيديو.\n\nإذا صديقك طلب عن طريقك:\nله خصم 1 دينار\nولك خصم 1 دينار على طلبك القادم 🎁",
                "success_metric_48h": "10+ أسئلة = المنتج قوي 🟢 | 5-9 = عدّل الفيديو 🟡 | 1-4 = جرّب زاوية ثانية 🟠 | 0 = لا تشتري كمية 🔴"
            })
        else:
            scripts.append({
                "hook_type": "Generic Problem/Solution",
                "visual_timeline": {"0-2s": "المشكلة", "2-5s": "استخدام المنتج", "5-10s": "النتيجة"},
                "organic_caption": "الحل الأمثل! 🌟",
                "success_metric_48h": "راقب التفاعل"
            })

        viral_data.append({
            "product_name": product_name,
            "category": cat,
            "price": price,
            "viral_video_scripts": scripts
        })

    OUTPUT_FILE.write_text(
        json.dumps(viral_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # طباعة الاستراتيجية بشكل مرتب
    for v in viral_data:
        print("=" * 60)
        print(f"📦 Product: {v['product_name']} ({v['price']} JOD)\n")
        
        for i, script in enumerate(v['viral_video_scripts'], 1):
            print(f"🎬 Script {i} [{script['hook_type']}]:")
            
            if 'visual_timeline' in script:
                print("   🎥 Visuals:")
                for t, desc in script['visual_timeline'].items():
                    print(f"      {t}: {desc}")
                    
            if 'on_screen_text' in script:
                print("   📝 On-Screen Text:")
                for t, txt in script['on_screen_text'].items():
                    print(f"      {t}: {txt}")
                    
            if 'organic_caption' in script:
                print(f"\n   📱 Organic Caption:\n   {script['organic_caption']}")
                
            if 'in_box_card' in script:
                print(f"\n   🎁 In-the-box Card Text:\n   {script['in_box_card']}")
                
            if 'success_metric_48h' in script:
                print(f"\n   📊 Success Metric (48h):\n   {script['success_metric_48h']}")
        print()

    print("✅ Saved viral strategy to viral_strategy.json")

if __name__ == "__main__":
    main()
