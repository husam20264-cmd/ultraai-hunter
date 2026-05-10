import json
from pathlib import Path
import random

INPUT_FILE = Path("product_winners_clean.json")
OUTPUT_FILE = Path("ad_creatives.json")

# الآن كل منتج له مميزاته الخاصة ومشكلته الخاصة
CREATIVE_DB = {
    "Kitchen Essentials": [
        {
            "name_ar": "طقم أدوات مطبخ معلق يوفر المساحة",
            "problem": "فوضى وازدحام المطبخ",
            "benefits": ["يوفر 50% من مساحة المطبخ", "كل الأدوات بيدك في ثانية", "تصميم أنيق يضفي لمسة عصرية"],
            "hooks_ar": ["مطبخك صغير ومزدحم؟ هذا الحل رهيب! 🤯", "سر المطابخ المرتبة أخيراً انكشف 🤫"]
        },
        {
            "name_ar": "منظم أدراج المطبخ الذكي",
            "problem": "توهان الأدوات داخل الأدراج",
            "benefits": ["كل شيء له مكان محدد", "تلاقي اللي بدك إياه بثواني", "يناسب كل أحجام الأدراج"],
            "hooks_ar": ["تتوهي بدك تلاقي المعلقة؟ 🥄😱", "الأدراج مش هتبقى نفس الشي بعد اليوم ✨"]
        },
        {
            "name_ar": "حامل توابل دوار 360 درجة",
            "problem": "فوضى أكياس البهارات في المطبخ",
            "benefits": ["كل البهارات أمامك بلفة واحدة", "يوفر مساحة كبيرة على الطاولة", "تصميم شفاف يعطي منظر مرتب"],
            "hooks_ar": ["البهارات مبعثرة بكل مكان؟ 🌶️🤯", "حوّلي فوضى المطبخ لترتيب في ثواني ✨"]
        }
    ],
    "Kitchen Tools & Gadgets": [
        {
            "name_ar": "مفرمة خضار كهربائية متعددة الاستخدامات",
            "problem": "تقطيع الخضار لساعات",
            "benefits": ["تقطع كمية كبيرة في 10 ثواني", "آمنة 100% على الأصابع", "سهلة التنظيف بالماء"],
            "hooks_ar": ["تعبتِ من تقطيع الخضار لساعات؟ 🥕🔪", "مطبخك يستاهل أسهل! اكتشفي الأداة السحرية 🪄"]
        },
        {
            "name_ar": "قاطع بصل مبتكر لا يدمع العين",
            "problem": "دموع العين ورائحة البصل",
            "benefits": ["يقطع البصل بدون ما تحسي بشي", "شرائح متساوية ومثالية", "غلق محكم يمنع تسرب الرائحة"],
            "hooks_ar": ["البصل يدمع عينك؟ خلصت المشكلة! 🧅😡", "أسرع طريقة لتقطيع البصل بدون دموع 💧"]
        },
        {
            "name_ar": "عجان طعام ومفرمة يدوية 7 في 1",
            "problem": "تعدد الأدوات وصعوبة التحضير",
            "benefits": ["يغنيك عن 7 أجهزة في المطبخ", "مثالي للعجن والفرم والتقطيع", "يدوي وبدون حاجة للكهرباء"],
            "hooks_ar": ["وفّري ساعة يومياً في المطبخ مع هذا الاختراع ⏰", "7 أجهزة في واحد! هل تصدق؟ 🤯"]
        }
    ],
    "Car Accessories": [
        {
            "name_ar": "حامل جوال مغناطيسي للسيارة 360 درجة",
            "problem": "تشتت الانتباه وسقوط الجوال أثناء القيادة",
            "benefits": ["تثبيت مغناطيسي قوي 100%", "يدور 360 درجة لكل الزوايا", "سهل التركيب بدون أدوات"],
            "hooks_ar": ["جوالك يطير وأنت تقود؟ خلصت المشكلة 📱🚗", "أهم اكسسوار ممكن تشتريه لسيارتك الحين! 🔥"]
        },
        {
            "name_ar": "مكنسة سيارة لاسلكية قوية الشفط",
            "problem": "الأوساخ والفتات داخل السيارة",
            "benefits": ["شفط قوي ينظف كل الزوايا", "لاسلكي وخفيف الوزن", "يشحن بسهولة في السيارة"],
            "hooks_ar": ["سيارتك مليانة أوساخ وففتات؟ 🤢🚗", "نظّف سيارتك في دقيقتين بدون مكنسة كبيرة ✨"]
        },
        {
            "name_ar": "منظم حاجيات السيارة خلف المقعد",
            "problem": "فوضى الأغراض وعدم وجود مساحة",
            "benefits": ["يستوعب المياه والمناديل والألعاب", "مضاد للماء وسهل التنظيف", "يركب في ثواني على أي مقعد"],
            "hooks_ar": ["الأغراض مبعثرة في السيارة؟ 👶🚗", "اللي بأبغاه بأجيب بثواني! الحل النهائي ✨"]
        }
    ]
}

AD_TEMPLATE_AR = """
🔥 {hook}

مشكلتنا مع {problem} انتهت! 🎉
الآن مع: {product_name}

✅ {benefit_1}
✅ {benefit_2}
✅ {benefit_3}

💰 السعر: {price} دينار فقط (التوصيل متوفر في عمان والأردن 🇯🇴)

اطلب الآن قبل ما يخلص المخزون! 👇
[رابط الطلب]
"""

def main():
    if not INPUT_FILE.exists():
        print("❌ Run product_purifier.py first!")
        return

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    creatives = []

    print("🎨 Generating Ad Creatives...\n")

    for item in data:
        cat_name = item["clean_product_name"]
        price = item.get("avg_price_jod", 0)
        
        if cat_name not in CREATIVE_DB:
            continue

        # اختيار منتج عشوائي بقصته الخاصة
        product_data = random.choice(CREATIVE_DB[cat_name])
        hook = random.choice(product_data["hooks_ar"])

        ad_text = AD_TEMPLATE_AR.format(
            hook=hook,
            problem=product_data["problem"],
            product_name=product_data["name_ar"],
            benefit_1=product_data["benefits"][0],
            benefit_2=product_data["benefits"][1],
            benefit_3=product_data["benefits"][2],
            price=price
        )

        creatives.append({
            "category": cat_name,
            "suggested_product_ar": product_data["name_ar"],
            "ad_copy_ar": ad_text.strip(),
            "suggested_price_jod": price
        })

    OUTPUT_FILE.write_text(
        json.dumps(creatives, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    for c in creatives:
        print("=" * 50)
        print(f"📦 Category: {c['category']}")
        print(f"💡 Suggested Product: {c['suggested_product_ar']}")
        print(f"💰 Price: {c['suggested_price_jod']} JOD\n")
        print(c['ad_copy_ar'])
        print()

    print(f"\n✅ Saved {len(creatives)} creatives to ad_creatives.json")

if __name__ == "__main__":
    main()


# ==========================================================
# Wrapper function for legacy UltraAI Dashboard (main.py)
# ==========================================================
def generate_ad_creative_pack(product_name, category="General", price=0):
    """
    Generates a list of ad creatives for the old dashboard to import.
    """
    import random
    
    # قوالب بسيطة للداشبورد القديم
    templates = [
        f"🔥 اكتشف {product_name} الآن! جودة عالية وسعر ممتاز.",
        f"✨ {product_name} بأفضل سعر. لا تفوت الفرصة!",
        f"🚀 {product_name} وصل للسوق الأردني. اطلبه الآن!"
    ]
    
    return [{
        "product_name": product_name,
        "category": category,
        "price_jod": price,
        "ad_copy_ar": random.choice(templates),
        "status": "Generated"
    }]
