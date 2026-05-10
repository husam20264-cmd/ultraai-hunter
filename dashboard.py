from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import uvicorn

app = FastAPI()

# تقديم مجلد الصور كملفات ثابتة
IMAGE_DIR = Path("ad_images")
IMAGE_DIR.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=str(IMAGE_DIR)), name="images")

# ==========================================
# API Endpoints
# ==========================================

@app.get("/api/product-hunter")
async def get_hunter_data():
    final_file = Path("final_products.json")
    supplier_file = Path("supplier_options.json")
    
    if not final_file.exists():
        return {"status": "empty", "message": "Run python ultraai_pipeline.py first!"}
        
    products = json.loads(final_file.read_text(encoding="utf-8"))
    suppliers_data = {}
    
    if supplier_file.exists():
        sup_list = json.loads(supplier_file.read_text(encoding="utf-8"))
        for s in sup_list:
            suppliers_data[s["product_name_ar"]] = s.get("local_suppliers_jo", [])
            
    for p in products:
        p["local_suppliers"] = suppliers_data.get(p["product_name_ar"], [])
        
    return {"status": "success", "products": products}


# ==========================================
# HTML Pages
# ==========================================

HUNTER_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UltraAI Product Hunter</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #38bdf8; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #38bdf8; margin: 0 15px; text-decoration: none; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
        .card { background: #1e293b; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #334155; }
        .card img { width: 100%; height: 220px; object-fit: cover; background-color: #334155; }
        .card-content { padding: 15px; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-bottom: 10px; }
        .badge-ready { background: #22c55e; color: #052e16; }
        .badge-manual { background: #f97316; color: #fff; }
        .badge-nopic { background: #ef4444; color: #fff; }
        .price { font-size: 1.5em; color: #38bdf8; font-weight: bold; margin: 5px 0; }
        .ad-copy { background: #0f172a; padding: 10px; border-radius: 8px; font-size: 0.9em; white-space: pre-wrap; margin-top: 10px; max-height: 200px; overflow-y: auto; }
        .supplier { margin-top: 10px; font-size: 0.9em; }
        .supplier div { background: #334155; padding: 5px 10px; border-radius: 4px; margin-top: 5px; }
        .empty-msg { text-align: center; margin-top: 50px; font-size: 1.2em; color: #94a3b8; }
    </style>
</head>
<body>
    <h1>🚀 UltraAI Product Hunter</h1>
    <div class="nav">
        <a href="/">الرئيسية</a>
        <a href="/hunter">صائد المنتجات</a>
    </div>
    
    <div id="products-container" class="grid">
        <div class="empty-msg">جاري تحميل المنتجات...</div>
    </div>

    <script>
        fetch('/api/product-hunter')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('products-container');
                
                if (data.status === 'empty') {
                    container.innerHTML = `<div class="empty-msg">لا توجد منتجات نهائية بعد. شغّل: <b>python ultraai_pipeline.py</b></div>`;
                    return;
                }
                
                container.innerHTML = '';
                
                data.products.forEach(product => {
                    // تحديد حالة الـ Badge
                    let badgeClass = 'badge-nopic';
                    let badgeText = '🔴 يحتاج صورة يدوية';
                    
                    if (product.status === '🟢 Ready for Ad') {
                        badgeClass = 'badge-ready';
                        badgeText = '🟢 جاهز للإطلاق';
                    } else if (product.status === '🟡 Needs Product Image') {
                        badgeClass = 'badge-manual';
                        badgeText = '🟡 يحتاج صورة يدوية';
                    }

                    // تحديد رابط الصورة (محلي أو Placeholder)
                    let imgSrc = 'https://via.placeholder.com/320x220/1e293b/94a3b8?text=Needs+Manual+Image';
                    
                    if (product.local_image_path && product.local_image_path !== 'NO_LOCAL_IMAGE') {
                        // استخراج اسم الملف فقط من المسار
                        const filename = product.local_image_path.split('/').pop();
                        imgSrc = '/images/' + filename;
                    } else if (product.image_url && product.image_url !== 'NO_IMAGE_FOUND') {
                        // اللجوء للرابط الخارجي فقط إذا كان متوفراً وليس خاطئاً
                        // imgSrc = product.image_url; // مفعل لو أردت تجربة الروابط الخارجية
                    }

                    // الموردين
                    let suppliersHTML = '';
                    if (product.local_suppliers && product.local_suppliers.length > 0) {
                        suppliersHTML = `<div class="supplier"><b>🏭 موردين محليين:</b>` + 
                            product.local_suppliers.map(s => `<div>${s.title}</div>`).join('') + `</div>`;
                    }

                    container.innerHTML += `
                        <div class="card">
                            <img src="${imgSrc}" alt="${product.product_name_ar}">
                            <div class="card-content">
                                <span class="badge ${badgeClass}">${badgeText}</span>
                                <h3>${product.product_name_ar}</h3>
                                <div class="price">${product.price_jod} JOD</div>
                                ${suppliersHTML}
                                <details>
                                    <summary style="color: #38bdf8; cursor: pointer; margin-top: 10px;">📝 النص الإعلاني</summary>
                                    <div class="ad-copy">${product.ad_copy_ar}</div>
                                </details>
                            </div>
                        </div>
                    `;
                });
            });
    </script>
</body>
</html>
"""

@app.get("/hunter", response_class=HTMLResponse)
async def hunter_dashboard():
    return HUNTER_HTML

@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    return "<h1>UltraAI Main Dashboard</h1><p>Go to <a href='/hunter'>/hunter</a> for Product Hunter Dashboard.</p>"

if __name__ == "__main__":
    print("🚀 Starting UltraAI Dashboard on http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
