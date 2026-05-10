from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json

router = APIRouter()

try:
    IMAGE_DIR = Path("ad_images")
    IMAGE_DIR.mkdir(exist_ok=True)
    router.mount("/ad_images", StaticFiles(directory=str(IMAGE_DIR)), name="ad_images")
except Exception as e:
    print(f"Warning: {e}")


@router.get("/api/product-hunter")
async def get_product_hunter_data():
    final_file = Path("final_products.json")
    supplier_file = Path("supplier_options.json")

    if not final_file.exists():
        return {"status": "empty", "message": "Run pipeline first!", "products": []}

    products = json.loads(final_file.read_text(encoding="utf-8"))
    suppliers_data = {}

    if supplier_file.exists():
        supplier_list = json.loads(supplier_file.read_text(encoding="utf-8"))
        for s in supplier_list:
            suppliers_data[s.get("product_name_ar")] = s.get("local_suppliers_jo", [])

    for p in products:
        p["local_suppliers"] = suppliers_data.get(p.get("product_name_ar"), [])

    return {"status": "success", "products": products}


HUNTER_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UltraAI Product Hunter</title>
    <style>
        body { font-family: sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:20px; }
        h1 { text-align:center; color:#38bdf8; }
        .nav { text-align:center; margin-bottom:20px; }
        .nav a { color:#94a3b8; margin:0 15px; text-decoration:none; font-weight:bold; }
        .grid { display:grid; grid-template-columns:1fr; gap:20px; max-width:900px; margin:auto; }
        @media (min-width: 760px) { .grid { grid-template-columns:repeat(auto-fill, minmax(330px, 1fr)); } }
        .card { background:#1e293b; border:1px solid #334155; border-radius:16px; overflow:hidden; }
        .card img { width:100%; height:220px; object-fit:cover; background:#334155; }
        .card-content { padding:18px; }
        .badge { display:inline-block; padding:5px 10px; border-radius:999px; font-size:.8em; font-weight:bold; margin-bottom:12px; }
        .badge-ready { background:#22c55e; color:#052e16; }
        .badge-manual { background:#f59e0b; color:#111827; }
        h3 { margin:6px 0; line-height:1.5; }
        .price { font-size:1.5em; color:#38bdf8; font-weight:900; margin:10px 0; }
        .supplier { margin-top:14px; font-size:.9em; }
        .supplier b { display: block; margin-bottom: 6px; color: #94a3b8; }
        .supplier div { background:#334155; padding:8px 12px; border-radius:8px; margin-top:6px; }
        .ad-copy { background:#0f172a; padding:14px; border-radius:10px; font-size:.92em; white-space:pre-wrap; margin-top:12px; max-height:240px; overflow:auto; line-height:1.8; border: 1px solid #334155; }
        details summary { color:#38bdf8; cursor:pointer; margin-top:14px; font-weight:bold; }
        .empty { text-align:center; margin:50px auto; max-width:500px; color:#94a3b8; background:#1e293b; padding:30px; border-radius:16px; border: 1px dashed #334155; }
    </style>
</head>
<body>
    <h1>🚀 UltraAI Product Hunter</h1>
    <div class="nav">
        <a href="/">🏠 الرئيسية</a>
        <a href="/hunter">🔍 صائد المنتجات</a>
    </div>
    <div id="products-container" class="grid">
        <div class="empty">⏳ Loading...</div>
    </div>
    <script>
        fetch('/api/product-hunter?t=' + Date.now())
            .then(r => r.json())
            .then(data => {
                const c = document.getElementById('products-container');
                if (data.status === 'empty' || !data.products || data.products.length === 0) {
                    c.innerHTML = '<div class="empty">No products yet. Run pipeline.</div>';
                    return;
                }
                c.innerHTML = '';
                data.products.forEach(p => {
                    const ready = p.status && p.status.includes('Ready');
                    const badgeClass = ready ? 'badge-ready' : 'badge-manual';
                    const badgeText = ready ? '🟢 Ready' : '🟡 Needs Image';
                    
                    let imgSrc = 'https://via.placeholder.com/330x220/1e293b/94a3b8?text=Needs+Image';
                    if (p.local_image_path && p.local_image_path !== 'NO_LOCAL_IMAGE') {
                        imgSrc = '/ad_images/' + p.local_image_path.split('/').pop();
                    }

                    let supHTML = '<div class="supplier"><b>Suppliers:</b><div>Manual check needed</div></div>';
                    if (p.local_suppliers && p.local_suppliers.length > 0) {
                        supHTML = '<div class="supplier"><b>Suppliers:</b>' + p.local_suppliers.map(s => '<div>' + (s.title || 'Supplier') + '</div>').join('') + '</div>';
                    }

                    c.innerHTML += '<div class="card"><img src="' + imgSrc + '"><div class="card-content"><span class="badge ' + badgeClass + '">' + badgeText + '</span><h3>' + p.product_name_ar + '</h3><div class="price">' + p.price_jod + ' JOD</div>' + supHTML + '<details><summary>📝 Ad Copy</summary><div class="ad-copy">' + (p.ad_copy_ar || 'N/A') + '</div></details></div></div>';
                });
            })
            .catch(e => {
                document.getElementById('products-container').innerHTML = '<div class="empty">Error loading data</div>';
            });
    </script>
</body>
</html>
"""


@router.get("/hunter", response_class=HTMLResponse)
async def product_hunter_dashboard():
    return HUNTER_HTML
