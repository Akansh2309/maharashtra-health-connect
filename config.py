# config.py — all the knobs in one place
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_PATH = os.path.join(BASE_DIR, "Disease_symptom_predictor.joblib")
DB_PATH = os.path.join(DATA_DIR, "hpo_database.db")

PORT = int(os.environ.get('PORT', 3000))

COOKIE_NAME = "mhc_session"
SESSION_TTL = 86400
SESSION_TTL_REMEMBER = 2592000

RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECS = 60

PUBLIC_PATHS = {
    "/login.html", "/final.html",
    "/api/login", "/api/register",
    "/api/predict", "/api/facilities",
    "/api/facilities/search", "/api/medicines/search",
    "/api/symptoms/search",
    "/favicon.ico",
}

PUBLIC_PREFIXES = ("/css/", "/js/", "/img/", "/assets/", "/api/")
