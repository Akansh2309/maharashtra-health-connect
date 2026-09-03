# config.py — all the knobs in one place
# easier to tweak port / cookie name / limits without hunting thru 5 files

import os

# where our static frontend lives (css, js, html)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# server
PORT = int(os.environ.get('PORT', 3000))

# cookie / session stuff
COOKIE_NAME = "mhc_session"
SESSION_TTL = 86400            # 24 hours
SESSION_TTL_REMEMBER = 2592000  # 30 days

# rate limiting — keeps brute-force bots out
RATE_LIMIT_MAX_REQUESTS = 5
RATE_LIMIT_WINDOW_SECS = 60

# pages that don't need login
PUBLIC_PATHS = {
    "/login.html",
    "/api/login",
    "/api/register",
    "/favicon.ico",
    "/img/hospital_logo.png",
    "/assets/logo.png",
}

# also let through anything under /css and /js
# (we check prefixes separately in auth_utils)
PUBLIC_PREFIXES = ("/css/", "/js/", "/img/", "/assets/")
