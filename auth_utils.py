import hashlib
import uuid
import time
from http.cookies import SimpleCookie


COOKIE_NAME = "mhc_session"
SESSION_TTL = 86400
SESSION_TTL_REMEMBER = 2592000

USERS = {
    "akansh": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Akansh Shaw",
        "role": "admin",
    },
    "demo": {
        "password_hash": hashlib.sha256("demo".encode()).hexdigest(),
        "name": "Demo User",
        "role": "user",
    },
}

SESSIONS = {}

AUTH_BYPASS_PATHS = {
    "/login.html",
    "/css/style.css",
    "/css/login.css",
    "/js/login.js",
    "/js/i18n.js",
    "/api/login",
    "/api/register",
    "/favicon.ico",
}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, stored_hash):
    return hash_password(password) == stored_hash


def create_session(username, remember=False):
    sid = str(uuid.uuid4())
    user = USERS[username]
    ttl = SESSION_TTL_REMEMBER if remember else SESSION_TTL
    SESSIONS[sid] = {
        "user": username,
        "name": user["name"],
        "role": user["role"],
        "expires": time.time() + ttl,
    }
    return sid, ttl


def validate_session(handler):
    cookie_header = handler.headers.get("Cookie", "")
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    morsel = cookie.get(COOKIE_NAME)
    if morsel:
        session = SESSIONS.get(morsel.value)
        if session and session.get("expires", 0) > time.time():
            return session
    return None


def destroy_session(handler):
    cookie_header = handler.headers.get("Cookie", "")
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    morsel = cookie.get(COOKIE_NAME)
    if morsel and morsel.value in SESSIONS:
        del SESSIONS[morsel.value]
        return True
    return False


def parse_cookies(cookie_header):
    cookie = SimpleCookie()
    cookie.load(cookie_header or "")
    return {key: morsel.value for key, morsel in cookie.items()}


def build_set_cookie(sid, ttl):
    return f"{COOKIE_NAME}={sid}; Path=/; Max-Age={ttl}; SameSite=Lax"


def build_expire_cookie():
    return f"{COOKIE_NAME}=; Path=/; Max-Age=0"


def register_user(username, password, name):
    username = username.strip().lower()

    if not username or not password or not name:
        return None, "All fields are required"

    if len(username) < 3:
        return None, "Username must be at least 3 characters"

    if len(password) < 4:
        return None, "Password must be at least 4 characters"

    if username in USERS:
        return None, "Username is already taken"

    USERS[username] = {
        "password_hash": hash_password(password),
        "name": name.strip(),
        "role": "user",
    }
    return username, None


def authenticate_user(username, password):
    username = username.strip().lower()
    user = USERS.get(username)
    if not user:
        return None, "Invalid credentials"
    if not verify_password(password, user["password_hash"]):
        return None, "Invalid credentials"
    return username, None


def get_session_info(session):
    if not session:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": session["user"],
        "name": session["name"],
        "role": session["role"],
    }


def is_path_protected(path):
    return path not in AUTH_BYPASS_PATHS
