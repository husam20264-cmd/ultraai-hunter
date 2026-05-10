from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import json
from pathlib import Path
import hashlib
import secrets

auth_router = APIRouter()

# ==========================================================
# Database Simulation (SQLite في النسخة التجارية)
# ==========================================================
USERS_FILE = Path("users_db.json")
if not USERS_FILE.exists():
    USERS_FILE.write_text(json.dumps({}, ensure_ascii=False), encoding="utf-8")

def load_users():
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    return secrets.token_hex(16)

# ==========================================================
# Models
# ==========================================================
class UserCreate(BaseModel):
    username: str
    password: str
    market: str = "Jordan" # السعودية، الإمارات، إلخ

class UserLogin(BaseModel):
    username: str
    password: str

# ==========================================================
# Auth Pages
# ==========================================================
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UltraAI - Login</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1e293b; padding: 30px; border-radius: 16px; width: 350px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
        h2 { text-align: center; color: #38bdf8; margin-top: 0; }
        .sub { text-align: center; color: #94a3b8; font-size: 0.9em; margin-bottom: 20px; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; background: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; font-size: 1em; }
        button:hover { background: #0ea5e9; }
        .error { color: #ef4444; text-align: center; font-size: 0.9em; display: none; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { flex: 1; text-align: center; padding: 10px; cursor: pointer; border-bottom: 2px solid transparent; color: #94a3b8; }
        .tab.active { color: #38bdf8; border-bottom-color: #38bdf8; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🚀 UltraAI</h2>
        <div class="sub">Product Hunter Platform</div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('login')">تسجيل الدخول</div>
            <div class="tab" onclick="switchTab('register')">حساب جديد</div>
        </div>

        <div id="error" class="error"></div>

        <form id="authForm">
            <input type="text" id="username" placeholder="اسم المستخدم" required>
            <input type="password" id="password" placeholder="كلمة المرور" required>
            
            <div id="marketField" style="display:none;">
                <select id="market">
                    <option value="Jordan">🇯🇴 الأردن</option>
                    <option value="Saudi Arabia">🇸🇦 السعودية</option>
                    <option value="UAE">🇦🇪 الإمارات</option>
                    <option value="Egypt">🇪🇬 مصر</option>
                </select>
            </div>

            <button type="submit" id="submitBtn">دخول</button>
        </form>
    </div>

    <script>
        let currentTab = 'login';
        
        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            if(tab === 'login') {
                document.querySelectorAll('.tab')[0].classList.add('active');
                document.getElementById('marketField').style.display = 'none';
                document.getElementById('submitBtn').innerText = 'دخول';
            } else {
                document.querySelectorAll('.tab')[1].classList.add('active');
                document.getElementById('marketField').style.display = 'block';
                document.getElementById('submitBtn').innerText = 'إنشاء حساب';
            }
        }

        document.getElementById('authForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const market = document.getElementById('market').value;
            const errorDiv = document.getElementById('error');

            const endpoint = currentTab === 'login' ? '/auth/login' : '/auth/register';
            const body = currentTab === 'login' ? {username, password} : {username, password, market};

            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(body)
                });
                
                const data = await res.json();
                
                if(data.token) {
                    localStorage.setItem('ultraai_token', data.token);
                    localStorage.setItem('ultraai_user', username);
                    localStorage.setItem('ultraai_market', data.market || 'Jordan');
                    window.location.href = '/hunter';
                } else {
                    errorDiv.textContent = data.detail || 'حدث خطأ';
                    errorDiv.style.display = 'block';
                }
            } catch (err) {
                errorDiv.textContent = 'خطأ في الاتصال';
                errorDiv.style.display = 'block';
            }
        });
    </script>
</body>
</html>
"""

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page():
    return LOGIN_HTML

# ==========================================================
# Auth API Endpoints
# ==========================================================
@auth_router.post("/auth/register")
async def register(user: UserCreate):
    users = load_users()
    
    if user.username in users:
        raise HTTPException(status_code=400, detail="اسم المستخدم موجود مسبقاً")
    
    token = generate_token()
    users[user.username] = {
        "password_hash": hash_password(user.password),
        "market": user.market,
        "plan": "free", # free أو pro
        "scans_today": 0,
        "token": token
    }
    
    save_users(users)
    
    # إنشاء مجلد بيانات خاص بالمستخدم
    user_dir = Path(f"user_data/{user.username}")
    user_dir.mkdir(parents=True, exist_ok=True)
    
    return {"message": "تم إنشاء الحساب بنجاح", "token": token, "market": user.market}

@auth_router.post("/auth/login")
async def login(user: UserLogin):
    users = load_users()
    
    if user.username not in users:
        raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور خاطئة")
    
    if users[user.username]["password_hash"] != hash_password(user.password):
        raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور خاطئة")
    
    # تجديد التوكن عند كل دخول
    new_token = generate_token()
    users[user.username]["token"] = new_token
    save_users(users)
    
    return {"message": "تم الدخول بنجاح", "token": new_token, "market": users[user.username]["market"]}

# Middleware للتحقق من تسجيل الدخول
async def get_current_user(request: Request):
    token = request.cookies.get("token") or request.query_params.get("token")
    
    if not token:
        # في الواجهة، سنرسل التوكن من localStorage
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(status_code=401, detail="يجب تسجيل الدخول أولاً")
        
    users = load_users()
    for username, data in users.items():
        if data.get("token") == token:
            return {"username": username, "market": data["market"], "plan": data["plan"]}
            
    raise HTTPException(status_code=401, detail="جلسة غير صالحة، سجل دخولك مجدداً")
