# auth_utils.py — handles users, passwords, sessions, cookies, rate-limiting
# basically everything related to "who are you and can you be here?"

import hashlib
import uuid
import time
import threading
from http.cookies import SimpleCookie

from config import (
    COOKIE_NAME,
    SESSION_TTL,
    SESSION_TTL_REMEMBER,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECS,
    PUBLIC_PATHS,
    PUBLIC_PREFIXES,
)

# lock for writes — registration adds users, so we don't want two threads
# stepping on each other. reads are fine without it honestly
_write_lock = threading.Lock()

# ── mock user database ──────────────────────────────────
# in production you'd swap this for postgres/mongo/whatever
USERS = {
    "akansh": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Akansh Shaw",
        "email": "akansh@kacchodis.org",
        "role": "admin",
    },
    "demo": {
        "password_hash": hashlib.sha256("demo".encode()).hexdigest(),
        "name": "Demo User",
        "email": "demo@kacchodis.org",
        "role": "user",
    },
}

# active sessions — maps session_id -> {user, name, role, expires, ...}
SESSIONS = {}

# rate limit tracker — maps ip -> [timestamp, timestamp, ...]
_rate_hits = {}


# ── password helpers ────────────────────────────────────

def hash_pw(password):
    # sha256 is fine for a hackathon demo, but use bcrypt in real life
    return hashlib.sha256(password.encode()).hexdigest()


def check_pw(plain_text, hashed):
    return hash_pw(plain_text) == hashed


# ── session management ──────────────────────────────────

def create_session(username, remember=False):
    sid = str(uuid.uuid4())
    user = USERS[username]
    ttl = SESSION_TTL_REMEMBER if remember else SESSION_TTL

    SESSIONS[sid] = {
        "user": username,
        "name": user["name"],
        "email": user.get("email", ""),
        "role": user["role"],
        "expires": time.time() + ttl,
    }
    return sid, ttl


def get_session(handler):
    """Pull the session dict from the request cookie, or None if invalid."""
    raw = handler.headers.get("Cookie", "")
    jar = SimpleCookie()
    jar.load(raw)
    morsel = jar.get(COOKIE_NAME)

    if not morsel:
        return None

    sess = SESSIONS.get(morsel.value)
    # expired?
    if sess and sess["expires"] > time.time():
        return sess
    return None


def kill_session(handler):
    """Remove the session so the user is effectively logged out."""
    raw = handler.headers.get("Cookie", "")
    jar = SimpleCookie()
    jar.load(raw)
    morsel = jar.get(COOKIE_NAME)

    if morsel and morsel.value in SESSIONS:
        del SESSIONS[morsel.value]
        return True
    return False


def session_info(sess):
    """Returns a safe dict we can send to the frontend."""
    if not sess:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": sess["user"],
        "name": sess["name"],
        "email": sess.get("email", ""),
        "role": sess["role"],
    }


def purge_expired():
    """Called periodically by a background thread to clean stale sessions."""
    now = time.time()
    dead = [sid for sid, s in SESSIONS.items() if s["expires"] <= now]
    for sid in dead:
        del SESSIONS[sid]


# ── cookie builders ─────────────────────────────────────

def make_cookie(sid, ttl):
    # HttpOnly stops JS from reading the cookie (XSS protection)
    return f"{COOKIE_NAME}={sid}; Path=/; Max-Age={ttl}; SameSite=Lax; HttpOnly"


def expire_cookie():
    # setting max-age=0 tells the browser to delete it immediately
    return f"{COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly"


# ── authentication ──────────────────────────────────────

def authenticate(login_id, password):
    """
    Try to log in with either a username or email.
    Returns (username, None) on success, or (None, error_msg) on failure.
    """
    login_id = login_id.strip().lower()

    # first try direct username match
    target = None
    uname = None

    if login_id in USERS:
        target = USERS[login_id]
        uname = login_id
    else:
        # fall back to email lookup
        for u, data in USERS.items():
            if data.get("email", "").lower() == login_id:
                target = data
                uname = u
                break

    if not target:
        return None, "Invalid credentials"

    if not check_pw(password, target["password_hash"]):
        return None, "Invalid credentials"

    return uname, None


def register(username, email, password, name):
    """
    Create a new user account. All validation happens here so the
    caller (api_routes) doesn't need to worry about it.
    """
    username = username.strip().lower()
    email = email.strip().lower()

    # basic checks
    if not username or not password or not name or not email:
        return None, "All fields are required"
    if len(username) < 3:
        return None, "Username must be at least 3 characters"
    if len(password) < 4:
        return None, "Password must be at least 4 characters"

    with _write_lock:
        if username in USERS:
            return None, "Username is already taken"

        # also check duplicate emails while we're at it
        for u in USERS.values():
            if u.get("email", "").lower() == email:
                return None, "That email is already registered"

        USERS[username] = {
            "password_hash": hash_pw(password),
            "name": name.strip(),
            "email": email,
            "role": "user",
        }

    return username, None


# ── rate limiting ───────────────────────────────────────

def rate_limit_ok(ip):
    """Returns True if this IP still has requests left, False if blocked."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECS

    if ip not in _rate_hits:
        _rate_hits[ip] = []

    # throw out old timestamps
    _rate_hits[ip] = [t for t in _rate_hits[ip] if t > cutoff]

    if len(_rate_hits[ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    _rate_hits[ip].append(now)
    return True


# ── path protection ─────────────────────────────────────

def needs_auth(path):
    """Quick check — does this URL need the user to be logged in?"""
    if path in PUBLIC_PATHS:
        return False
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return False
    return True


# ── RBAC (role check) ──────────────────────────────────

def has_role(sess, role):
    """Check if user has the given role. Admins pass every check."""
    if not sess:
        return False
    if sess["role"] == "admin":
        return True
    return sess["role"] == role
