from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import json
import os
import traceback
from pathlib import Path
from run_ultraai_orchestrator import run_full_scan
from pdf_report_generator import generate_investment_report

app = FastAPI()
HISTORY_FILE = Path("history.json")

# --- منطق الاستنتاج الذكي ---
def normalize_name(name):
    return str(name or "").strip().lower().replace("_", " ").replace("-", " ")

def to_int_score(value, fallback=0):
    try:
        val = str(value).replace("%", "").strip()
        return int(float(val))
    except: return int(fallback)

def infer_supply_from_score(score):
    s = to_int_score(score)
    if s >= 75: return "Low / Early Competition"
    if s >= 50: return "Medium / Growing Market"
    return "High Competition / Saturated"

# --- واجهة المستخدم المطورة بنظام تشخيص الأخطاء ---
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>UltraAI v1.6.4 | Master Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root { --bg: #0f172a; --card: #1e293b; --primary: #3b82f6; --text: #f8fafc; --green: #4ade80; --red: #f87171; }
            body { font-family: sans-serif; background: var(--bg); color: var(--text); padding: 15px; margin: 0; }
            .container { max-width: 500px; margin: auto; }
            .card { background: var(--card); padding: 20px; border-radius: 16px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.05); }
            input { width: 100%; padding: 12px; margin-bottom: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
            button { background: var(--primary); color: white; border: none; padding: 14px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            .top-item { display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
            .quick-pdf { background: linear-gradient(135deg, var(--red), #b91c1c); color: white; padding: 18px; border-radius: 12px; text-align: center; margin-bottom: 20px; cursor: pointer; font-weight: 900; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align:center; color:var(--primary);">🚀 UltraAI Dashboard</h1>
            <div id="quickPdfBox" class="quick-pdf" onclick="downloadBestPdf()" style="display:none">📄 Download Best PDF Report</div>
            
            <div class="card">
                <h3>🔍 Analyze Product</h3>
                <input type="text" id="product" placeholder="Product Name (e.g. Neck Pillow)">
                <button onclick="runAnalysis()" id="btnText">Analyze Demand</button>
            </div>

            <div class="card">
                <h3>🏆 Results History</h3>
                <div id="topList"></div>
            </div>
        </div>

        <script>
            async function updateUI() {
                const tRes = await fetch('/api/top-products');
                const products = await tRes.json();
                const list = document.getElementById('topList');
                document.getElementById('quickPdfBox').style.display = (products.length > 0) ? 'block' : 'none';
                
                let html = '';
                products.slice(0, 5).forEach(p => {
                    html += `<div class="top-item"><div><b>${p.product_name}</b><br><small>${p.decision}</small></div><b style="color:var(--primary)">${p.score}%</b></div>`;
                });
                list.innerHTML = html || '<p style="opacity:0.5;text-align:center">No records found.</p>';
                return products;
            }

            async function runAnalysis() {
                const p = document.getElementById('product').value;
                if(!p) return alert("Please enter a product name");
                
                const btn = document.getElementById('btnText');
                btn.innerText = "⏳ Running Scan...";
                btn.disabled = true;

                try {
                    const res = await fetch(`/analyze?product=${encodeURIComponent(p)}&country=Jordan`);
                    const data = await res.json();
                    
                    if (data.status === "error") {
                        alert("Analysis Failed: " + data.message);
                    } else {
                        await updateUI();
                        alert("Analysis Completed Successfully!");
                    }
                } catch (e) {
                    alert("Server Connection Lost: " + e);
                } finally {
                    btn.innerText = "Analyze Demand";
                    btn.disabled = false;
                }
            }

            function downloadBestPdf() {
                window.location.href = "/api/best-product-report-latest";
            }
            window.onload = updateUI;
        </script>
    </body>
    </html>
    """

# --- Endpoints مع نظام الحماية ---

@app.get("/analyze")
async def analyze(product: str, country: str = "Jordan"):
    try:
        print(f"DEBUG | Starting Scan for: {product}")
        # استدعاء المحرك الحقيقي
        result = run_full_scan(product, country, "General")
        return {"status": "success", "product": product, "result": result}
    except Exception as e:
        err_msg = traceback.format_exc()
        print(f"CRITICAL ERROR IN SCAN:\n{err_msg}")
        return {"status": "error", "message": str(e)}

@app.get("/api/top-products")
async def get_top_products():
    if not HISTORY_FILE.exists(): return []
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
        unique = {}
        for i in history:
            name = normalize_name(i.get('product_name'))
            if name not in unique or i.get('score', 0) > unique[name].get('score', 0):
                unique[name] = i
        return sorted(unique.values(), key=lambda x: x.get('score', 0), reverse=True)
    except: return []

@app.get("/api/best-product-report-latest")
async def best_report_latest():
    products = await get_top_products()
    if not products: return {"error": "No history"}
    best = products[0]
    score = to_int_score(best.get("score", 0))
    supply_label = infer_supply_from_score(score)
    
    pdf_path = generate_investment_report(
        product_name=best.get("product_name"),
        country="Jordan",
        demand_result={"status": "history", "current_value": score},
        attention_result={"status": "history", "attention_score": score},
        competition_result={"market_saturation": supply_label, "supply_status": supply_label},
        triple_match_result={"decision": "PROMISING", "recommendation": "Test Small Budget", "confidence": score}
    )
    return FileResponse(pdf_path, media_type="application/pdf")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
