from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from pathlib import Path
import json
import secrets

magic_router = APIRouter()

USERS_FILE = Path("users_db.json")

def load_users():
    if not USERS_FILE.exists():
        return {}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")

class EmailRequest(BaseModel):
    email: str

@magic_router.post("/auth/request-magic-link")
async def request_magic_link(data: EmailRequest):
    """استقبال الإيميل وتوليد رابط سحري يظهر في شاشة السيرفر"""
    email = data.email.lower().strip()
    users = load_users()
    
    # توليد توكن خاص باللوجين
    login_token = secrets.token_urlsafe(16)
    
    # إذا المستخدم جديد، سجله
    if email not in users:
        users[email] = {
            "password_hash": "magic_link",
            "market": "Jordan",
            "plan": "free",
            "scans_today": 0,
            "token": login_token,
            "name": email.split("@")[0],
            "auth_method": "magic_link"
        }
    else:
        # إذا موجود، حدث التوكن
        users[email]["token"] = login_token
        
    save_users(users)
    
    # طباعة الرابط السحري في شاشة الـ Termux للمسؤول (أو لإرساله بالإيميل لاحقاً)
    magic_url = f"http://127.0.0.1:8000/auth/verify-magic?token={login_token}"
    print("\n" + "="*50)
    print(f"📧 Magic Link Requested for: {email}")
    print(f"🔗 Click this link to login:")
    print(magic_url)
    print("="*50 + "\n")
    
    return {"status": "sent", "message": "تم إنشاء الرابط السحري. تحقق من شاشة السيرفر (Termux) للحصول على الرابط."}


@magic_router.get("/auth/verify-magic")
async def verify_magic_link(token: str):
    """التحقق من التوكن وتسجيل الدخول"""
    users = load_users()
    
    # البحث عن المستخدم الذي يملك هذا التوكن
    logged_in_email = None
    for email, data in users.items():
        if data.get("token") == token:
            logged_in_email = email
            break
            
    if not logged_in_email:
        return HTMLResponse(content="<h1>Invalid or expired link</h1>", status_code=401)
        
    user_data = users[logged_in_email]
    
    # توجيه المستخدم لصفحة حفظ البيانات في المتصفح ثم الداشبورد
    redirect_url = f"/auth/success?token={token}&user={user_data.get('name', logged_in_email)}&market={user_data.get('market', 'Jordan')}"
    return RedirectResponse(url=redirect_url)
