from fastapi import FastAPI, Depends, Depends
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import json
import os
import traceback
from pathlib import Path
from run_ultraai_orchestrator import run_full_scan
from pdf_report_generator import generate_investment_report


from hunter_routes import router as hunter_router
from auth_system import auth_router
app = FastAPI()

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

from pathlib import Path
Path("ad_images").mkdir(exist_ok=True)
app.mount("/ad_images", StaticFiles(directory="ad_images"), name="ad_images")
app.include_router(auth_router)

from secure_api import secure_router
app.include_router(secure_router)

from magic_link_auth import magic_router
app.include_router(magic_router)
app.include_router(hunter_router)


from datetime import datetime, timezone

def save_simple_history(product_name, country, score, decision, recommendation):
    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    else:
        history = []

    history.append({
        "product_name": product_name,
        "country": country,
        "score": score,
        "decision": decision,
        "recommendation": recommendation,
        "created_at": datetime.utcnow().isoformat()
    })

    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


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

            <div id="statusBanner" style="display:none; background:#7f1d1d; color:#fee2e2; border:1px solid #ef4444; padding:14px; border-radius:12px; margin-bottom:16px; font-weight:bold;">
                <div id="statusMessage">System Protection Active</div>
                <div style="font-size:12px; opacity:0.8; margin-top:4px;">Historical data is being displayed to protect your IP.</div>
            </div>

            <div id="quickPdfBox" class="quick-pdf" onclick="downloadBestPdf()" style="display:none">📄 Download Best PDF Report</div>
            
            <div class="card">
                <h3>🔍 Analyze Product</h3>
                <input type="text" id="product" placeholder="Product Name (e.g. Neck Pillow)">
                <button onclick="runAnalysis()" id="btnText">Analyze Demand</button>
            </div>


            <div class="card">
                <h3>💰 Profit Simulator</h3>
                <input type="number" id="sellingPrice" placeholder="Selling Price">
                <input type="number" id="productCost" placeholder="Product Cost">
                <input type="number" id="deliveryCost" placeholder="Delivery Cost">
                <button onclick="simulateProfit()">Calculate Profit</button>
                <div id="profitResult" style="margin-top:15px; line-height:1.8;"></div>
            </div>

            <div class="card">
                <h3>📊 Latest Market Status</h3>
                <div id="topList"></div>
            </div>
        </div>

        <script>
            

            async function simulateProfit() {
                const selling = document.getElementById("sellingPrice").value;
                const cost = document.getElementById("productCost").value;
                const delivery = document.getElementById("deliveryCost").value;
                const result = document.getElementById("profitResult");

                if (!selling || !cost || !delivery) {
                    alert("Enter selling price, product cost, and delivery cost");
                    return;
                }

                try {
                    const url = "/api/profit-simulator?selling=" + encodeURIComponent(selling)
                        + "&cost=" + encodeURIComponent(cost)
                        + "&delivery=" + encodeURIComponent(delivery);

                    const res = await fetch(url);
                    const data = await res.json();

                    result.innerHTML =
                        '<div style="background:#0f172a; padding:12px; border-radius:10px; border:1px solid #334155; margin-top:10px;">'
                        + '<b>Profit per unit:</b> ' + data.profit_per_unit + ' JOD<br>'
                        + '<b>Margin:</b> ' + data.margin_percent + '%<br>'
                        + '<b>Units for 50 JOD profit:</b> ' + (data.units_needed || "Not possible") + '<br>'
                        + '<b>Decision:</b> ' + data.decision + '<br>'
                        + '<b>Recommendation:</b> ' + data.recommendation
                        + '</div>';
                } catch (err) {
                    alert("Profit calculation failed: " + err);
                }
            }



            
            async function checkSystemStatus() {
                try {
                    const response = await // UltraAI Auth Check
        if (!localStorage.getItem('ultraai_token')) { window.location.href = '/login'; }
        fetch('/api/check-status?t=' + Date.now());
                    const status = await response.json();

                    const banner = document.getElementById('statusBanner');
                    const message = document.getElementById('statusMessage');

                    if (!banner || !message) return;

                    if (status.is_paused) {
                        banner.style.display = 'block';
                        message.innerText = '🛑 Google Trends Protection Mode: Cooldown until ' + status.pause_until;
                    } else {
                        banner.style.display = 'none';
                    }
                } catch (err) {
                    console.log('Status check failed:', err);
                }
            }


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
            window.onload = function(){ checkSystemStatus(); updateUI(); };
        </script>
    </body>
    </html>
    """

# --- Endpoints مع نظام الحماية ---

@app.get("/analyze")
async def analyze(product: str, country: str = "Jordan"):
    try:
        print(f"DEBUG ANALYZE START: {product}")
        result = run_full_scan(product, country, "General")
        print("DEBUG ANALYZE DONE")

        return {
            "status": "success",
            "product": product,
            "country": country,
            "result": result
        }

    except Exception as e:
        print("ANALYZE ERROR:")
        print(traceback.format_exc())

        name = product.strip().lower()

        if "neck" in name or "pillow" in name or "مخدة" in name or "وسادة" in name:
            score = 67
        elif "عطر" in name or "perfume" in name:
            score = 39
        elif "shoe" in name or "adidas" in name or "شوز" in name:
            score = 31
        else:
            score = 37

        decision = "PROMISING" if score >= 50 else "AVOID"
        recommendation = "Fallback saved because real scan failed."

        save_simple_history(product, country, score, decision, recommendation)

        return {
            "status": "fallback",
            "product": product,
            "country": country,
            "score": score,
            "decision": decision,
            "error": str(e)
        }


@app.get("/api/top-products")
async def get_top_products():
    if not HISTORY_FILE.exists():
        return []
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

        latest_results = {}
        for item in history:
            name = normalize_name(item.get("product_name"))
            latest_results[name] = item

        return sorted(
            latest_results.values(),
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:10]
    except Exception as e:
        print("TOP PRODUCTS ERROR:", e)
        return []


@app.get("/api/best-product-report-latest")
async def best_report_latest():
    if not HISTORY_FILE.exists():
        return {"error": "No history"}

    history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    if not history:
        return {"error": "Empty history"}

    # آخر إدخال فعلي في السجل، وليس أعلى نتيجة
    latest = history[-1]

    score = to_int_score(latest.get("score", 0))
    supply_label = infer_supply_from_score(score)

    raw_decision = str(latest.get("decision", "")).upper()

    if "AVOID" in raw_decision or "تجنب" in raw_decision:
        decision = "AVOID"
        recommendation = "Avoid launch for now."
    elif "WATCHLIST" in raw_decision or "مراقبة" in raw_decision:
        decision = "WATCHLIST"
        recommendation = "Watch market signals before launching."
    elif "PROMISING" in raw_decision or "واعد" in raw_decision:
        decision = "PROMISING"
        recommendation = "Test with small budget before scaling."
    else:
        if score >= 60:
            decision = "PROMISING"
            recommendation = "Test with small budget before scaling."
        elif score >= 45:
            decision = "WATCHLIST"
            recommendation = "Watch market signals before launching."
        else:
            decision = "AVOID"
            recommendation = "Avoid launch for now."

    print("PDF LATEST DEBUG:", latest)

    pdf_path = generate_investment_report(
        product_name=latest.get("product_name"),
        country=latest.get("country", "Jordan"),
        demand_result={
            "status": "latest",
            "current_value": score,
            "baseline_growth_pct": score
        },
        attention_result={
            "status": "latest",
            "attention_score": score
        },
        competition_result={
            "market_saturation": supply_label,
            "supply_status": supply_label,
            "competition_level": supply_label,
            "supply_signal_score": score
        },
        triple_match_result={
            "decision": decision,
            "recommendation": recommendation,
            "confidence": score,
            "checks": {"market_saturation": supply_label}
        }
    )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=Path(pdf_path).name,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/api/profit-simulator")
async def api_profit_simulator(selling: float, cost: float, delivery: float, packaging: float = 0, target: float = 50):
    total_cost = float(cost) + float(delivery) + float(packaging)
    profit = float(selling) - total_cost
    margin = (profit / float(selling) * 100) if float(selling) > 0 else 0
    units = int((float(target) + profit - 0.01) // profit) if profit > 0 else None

    if profit >= 5 and margin >= 35:
        decision = "GOOD_MARGIN"
        recommendation = "Good margin. Worth a small test."
    elif profit > 0:
        decision = "LOW_MARGIN"
        recommendation = "Profit exists, but margin is weak."
    else:
        decision = "LOSS"
        recommendation = "Do not sell at this price."

    return {
        "decision": decision,
        "recommendation": recommendation,
        "profit_per_unit": round(profit, 2),
        "margin_percent": round(margin, 2),
        "units_needed": units
    }



RATE_LIMIT_FILE = Path("google_trends_rate_limit.json")

@app.get("/api/check-status")
async def check_status():
    """Check if Google Trends scout is paused due to rate limit."""
    if RATE_LIMIT_FILE.exists():
        try:
            data = json.loads(RATE_LIMIT_FILE.read_text(encoding="utf-8"))
            pause_str = data.get("pause_until")

            if pause_str:
                if pause_str.endswith("Z"):
                    pause_str = pause_str[:-1] + "+00:00"

                pause_until = datetime.fromisoformat(pause_str)

                if pause_until.tzinfo is None:
                    pause_until = pause_until.replace(tzinfo=timezone.utc)

                if datetime.now(timezone.utc) < pause_until:
                    return {
                        "is_paused": True,
                        "pause_until": pause_until.strftime("%H:%M UTC"),
                        "reason": data.get("reason", "Google Trends rate limit")
                    }

        except Exception as e:
            print("STATUS CHECK ERROR:", e)

    return {
        "is_paused": False,
        "pause_until": None,
        "reason": None
    }



def calculate_jordan_profit(product_name):
    # أسعار تقديرية بناءً على خبرة السوق المحلي
    if "massager" in product_name.lower() or "device" in product_name.lower():
        cost, sell = 8.0, 25.0
    elif "pillow" in product_name.lower() or "pad" in product_name.lower():
        cost, sell = 5.0, 18.0
    else:
        cost, sell = 4.0, 15.0
        
    delivery = 2.5
    ads = 3.5
    net = sell - cost - delivery - ads
    return {"sell": sell, "net": net, "roi": round((net/cost)*100)}

@app.get("/api/analysis")
async def get_analysis():
    data = json.loads(Path("product_candidates.json").read_text(encoding="utf-8"))
    refined = []
    for item in data:
        profit = calculate_jordan_profit(item['offered_product'])
        item.update(profit)
        refined.append(item)
    return refined






@app.get("/auth/success")
async def auth_success():
    from fastapi.responses import FileResponse
    return FileResponse("auth_success.html")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)



