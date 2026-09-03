# security.py
# ---------------------------------------------------------
# Security Module for Maharashtra Health Connect
# Handles Authentication, Cookies, Sessions, and Permissions
# ---------------------------------------------------------

import hashlib
import uuid
import time
from http.cookies import SimpleCookie

# --- CONFIGURATION ---
COOKIE_NAME = "mhc_session_secure"
SESSION_TTL = 86400           # 1 Day in seconds
SESSION_TTL_REMEMBER = 2592000 # 30 Days in seconds

# --- DATABASE MOCK (Users with Email & Roles) ---
USERS = {
    "akansh": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Akansh Shaw",
        "email": "akansh@kacchodis.org",
        "role": "admin", # Admin can access everything
    },
    "demo": {
        "password_hash": hashlib.sha256("demo".encode()).hexdigest(),
        "name": "Demo User",
        "email": "demo@kacchodis.org",
        "role": "user",  # Normal user
    },
}

# --- IN-MEMORY SESSION STORE ---
SESSIONS = {}

# --- RATE LIMITING STORE (Super Security) ---
RATE_LIMIT_STORE = {}
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60 # seconds

# --- PUBLIC ENDPOINTS (No login required) ---
AUTH_BYPASS_PATHS = {
    "/login.html",
    "/css/style.css",
    "/css/login.css",
    "/js/login.js",
    "/js/i18n.js",
    "/api/login",
    "/api/register",
    "/favicon.ico",
    "/img/hospital_logo.png",
}

# ---------------------------------------------------------
# CORE SECURITY FUNCTIONS
# ---------------------------------------------------------

def check_rate_limit(ip_address: str) -> bool:
    """Simple rate limiter to block IPs exceeding max requests in a time window."""
    now = time.time()
    
    if ip_address not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[ip_address] = []
        
    # Clean old requests
    RATE_LIMIT_STORE[ip_address] = [
        req_time for req_time in RATE_LIMIT_STORE[ip_address] 
        if now - req_time < RATE_LIMIT_WINDOW
    ]
    
    if len(RATE_LIMIT_STORE[ip_address]) >= RATE_LIMIT_MAX:
        return False
        
    RATE_LIMIT_STORE[ip_address].append(now)
    return True

def hash_password(password: str) -> str:
    """Hashes a plain text password using SHA-256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, stored_hash: str) -> bool:
    """Compares a plain text password against a stored hash."""
    return hash_password(password) == stored_hash

def create_session(username: str, remember: bool = False) -> tuple:
    """Creates a new secure session for the user and stores it in memory."""
    sid = str(uuid.uuid4())
    user = USERS[username]
    ttl = SESSION_TTL_REMEMBER if remember else SESSION_TTL
    
    # Store session details including role for RBAC
    SESSIONS[sid] = {
        "user": username,
        "name": user["name"],
        "email": user.get("email", ""),
        "role": user["role"],
        "expires": time.time() + ttl,
    }
    return sid, ttl

def validate_session(handler) -> dict:
    """Reads the cookie from the HTTP request and validates the session."""
    cookie_header = handler.headers.get("Cookie", "")
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    morsel = cookie.get(COOKIE_NAME)
    
    # Check if session exists and is not expired
    if morsel:
        session = SESSIONS.get(morsel.value)
        if session and session.get("expires", 0) > time.time():
            return session
    return None

def destroy_session(handler) -> bool:
    """Logs a user out by removing their session from memory."""
    cookie_header = handler.headers.get("Cookie", "")
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    morsel = cookie.get(COOKIE_NAME)
    
    if morsel and morsel.value in SESSIONS:
        del SESSIONS[morsel.value]
        return True
    return False

# ---------------------------------------------------------
# COOKIE MANAGEMENT
# ---------------------------------------------------------

def build_set_cookie(sid: str, ttl: int) -> str:
    """Builds a Set-Cookie header string for a successful login."""
    # Using HttpOnly flag for security (prevents XSS attacks on cookies)
    return f"{COOKIE_NAME}={sid}; Path=/; Max-Age={ttl}; SameSite=Lax; HttpOnly"

def build_expire_cookie() -> str:
    """Builds a Set-Cookie header string to instantly expire a cookie (Logout)."""
    return f"{COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly"

# ---------------------------------------------------------
# AUTHENTICATION & REGISTRATION
# ---------------------------------------------------------

def register_user(username: str, email: str, password: str, name: str) -> tuple:
    """Registers a new user, checking for duplicates by username or email."""
    username = username.strip().lower()
    email = email.strip().lower()

    if not username or not password or not name or not email:
        return None, "All fields are required"

    if len(username) < 3:
        return None, "Username must be at least 3 characters"

    if len(password) < 4:
        return None, "Password must be at least 4 characters"

    if username in USERS:
        return None, "Username is already taken"
        
    # Check if email is already used
    for u in USERS.values():
        if u.get("email") == email:
            return None, "Email address is already in use"

    # Add user to mock DB
    USERS[username] = {
        "password_hash": hash_password(password),
        "name": name.strip(),
        "email": email,
        "role": "user", # Default role is 'user'
    }
    return username, None

def authenticate_user(login_id: str, password: str) -> tuple:
    """Authenticates a user by checking either their username or email."""
    login_id = login_id.strip().lower()
    
    # Find user by username OR email
    target_user = None
    target_username = None
    
    if login_id in USERS:
        target_user = USERS[login_id]
        target_username = login_id
    else:
        # Search by email
        for uname, udata in USERS.items():
            if udata.get("email") == login_id:
                target_user = udata
                target_username = uname
                break
                
    if not target_user:
        return None, "Invalid credentials"
        
    # Verify password hash
    if not verify_password(password, target_user["password_hash"]):
        return None, "Invalid credentials"
        
    return target_username, None

# ---------------------------------------------------------
# PERMISSIONS & ROLES (RBAC)
# ---------------------------------------------------------

def has_permission(session: dict, required_role: str) -> bool:
    """
    Checks if the user has the required permission role.
    Admin overrides all roles.
    """
    if not session:
        return False
        
    user_role = session.get("role", "user")
    if user_role == "admin":
        return True # Admin can do anything
        
    return user_role == required_role

def get_session_info(session: dict) -> dict:
    """Returns safe session information for the frontend."""
    if not session:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": session["user"],
        "name": session["name"],
        "email": session.get("email", ""),
        "role": session["role"],
    }

def is_path_protected(path: str) -> bool:
    """Determines if a URL path requires authentication."""
    if path in AUTH_BYPASS_PATHS:
        return False
    # Check if path starts with any allowed public paths
    for bypass in AUTH_BYPASS_PATHS:
        if path.startswith(bypass):
            return False
    return True
