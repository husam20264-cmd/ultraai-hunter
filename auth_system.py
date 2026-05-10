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
        .login-box { background: #1e293b; padding: 30px; border-radius: 16px; width: 380px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
        h2 { text-align: center; color: #38bdf8; margin-top: 0; }
        .sub { text-align: center; color: #94a3b8; font-size: 0.9em; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; font-size: 1em; }
        button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; background: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; font-size: 1em; }
        button:hover { background: #0ea5e9; }
        button:disabled { background: #334155; color: #94a3b8; cursor: not-allowed; }
        .msg { text-align: center; font-size: 0.9em; margin-top: 15px; padding: 10px; border-radius: 8px; display: none; }
        .msg-success { background: #052e16; color: #22c55e; border: 1px solid #22c55e; }
        .msg-error { background: #450a0a; color: #ef4444; border: 1px solid #ef4444; }
        .alt-login { text-align: center; margin-top: 20px; }
        .alt-login a { color: #38bdf8; text-decoration: none; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🚀 UltraAI</h2>
        <div class="sub">Product Hunter Platform</div>
        
        <form id="magicForm">
            <label for="email">أدخل بريدك الإلكتروني</label>
            <input type="email" id="email" placeholder="your@email.com" required>
            <button type="submit" id="sendBtn">إرسال الرابط السحري ✨</button>
        </form>

        <div id="successMsg" class="msg msg-success">
            تم إنشاء الرابط! <br>تحقق من شاشة السيرفر (Termux) لنسخ الرابط ولوج الدخول.
        </div>
        <div id="errorMsg" class="msg msg-error"></div>

        <div class="alt-login">
            <a href="/login-password">تسجيل الدخول بكلمة مرور (للمسؤولين)</a>
        </div>
    </div>

    <script>
        document.getElementById('magicForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const btn = document.getElementById('sendBtn');
            const successMsg = document.getElementById('successMsg');
            const errorMsg = document.getElementById('errorMsg');
            
            btn.disabled = true;
            btn.innerText = 'جاري الإرسال...';
            successMsg.style.display = 'none';
            errorMsg.style.display = 'none';
            
            try {
                const res = await fetch('/auth/request-magic-link', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                });
                
                const data = await res.json();
                
                if(data.status === 'sent') {
                    successMsg.style.display = 'block';
                } else {
                    errorMsg.textContent = data.detail || 'حدث خطأ';
                    errorMsg.style.display = 'block';
                }
            } catch (err) {
                errorMsg.textContent = 'خطأ في الاتصال بالسيرفر';
                errorMsg.style.display = 'block';
            }
            
            btn.disabled = false;
            btn.innerText = 'إرسال الرابط السحري ✨';
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
