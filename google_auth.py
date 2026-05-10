from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from pathlib import Path
import json
import os

google_router = APIRouter()

def load_env():
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

load_env()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', 'MISSING_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'MISSING_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

USERS_FILE = Path("users_db.json")
def load_users():
    if not USERS_FILE.exists():
        return {}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))

def save_users(users):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


@google_router.get("/auth/google/login")
async def login_with_google(request: Request):
    redirect_uri = request.url_for('auth_google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@google_router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            return RedirectResponse(url='/login?error=google_failed')

        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        
        users = load_users()
        
        if email not in users:
            import secrets
            users[email] = {
                "password_hash": "google_oauth",
                "market": "Jordan",
                "plan": "free",
                "scans_today": 0,
                "token": secrets.token_hex(16),
                "name": name,
                "auth_method": "google"
            }
            save_users(users)
        
        local_token = users[email]["token"]
        response = RedirectResponse(url=f'/auth/success?token={local_token}&user={name}&market={users[email]["market"]}')
        return response

    except Exception as e:
        print(f"Google Auth Error: {e}")
        return RedirectResponse(url='/login?error=google_exception')
