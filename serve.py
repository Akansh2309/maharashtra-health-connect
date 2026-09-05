#!/usr/bin/env python3
# serve.py — Maharashtra Health Connect (Hacked Build)
# One command to rule them all: python3 serve.py

import http.server
import json
import os
import socketserver
import threading
import time
from urllib.parse import urlparse

import auth_utils
import api_routes
from config import PORT, PUBLIC_DIR


class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    # ── GET routes ──────────────────────────────────────
    def do_GET(self):
        path = urlparse(self.path).path

        # API endpoints
        if path == "/api/symptoms":
            return api_routes.handle_symptom_list(self)

        if path.startswith("/api/symptoms/search"):
            return api_routes.handle_symptoms_search(self, self.path)

        if path == "/api/facilities":
            return api_routes.handle_facilities(self)

        if path.startswith("/api/facilities/search"):
            return api_routes.handle_facilities_search(self)

        if path.startswith("/api/medicines/search"):
            return api_routes.handle_medicines_search(self)

        if path == "/api/referrals":
            return api_routes.handle_referrals_get(self)

        if path.startswith("/api/referrals/REF-"):
            ref_id = path.split("/")[-1]
            return api_routes.handle_referral_detail(self, ref_id)

        if path == "/api/appointments":
            return api_routes.handle_appointments_get(self)

        if path == "/api/followups":
            return api_routes.handle_followups_get(self)

        if path == "/api/dashboard":
            return api_routes.handle_dashboard(self)

        if path == "/api/session":
            return api_routes.handle_session(self)

        if path == "/api/logout":
            return api_routes.handle_logout(self)

        # ── static files ────────────────────────────────
        if path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/final.html")
            self.end_headers()
            return

        file_path = os.path.join(PUBLIC_DIR, path.lstrip("/"))
        if not os.path.exists(file_path):
            if path.startswith("/api/"):
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                try:
                    with open(os.path.join(PUBLIC_DIR, "404.html"), "rb") as f:
                        self.wfile.write(f.read())
                except:
                    self.wfile.write(b"404 Not Found")
            return

        super().do_GET()

    # ── POST routes ─────────────────────────────────────
    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if path == "/api/predict":
            return api_routes.handle_predict(self, body)

        if path == "/api/login":
            return api_routes.handle_login(self, body)

        if path == "/api/register":
            return api_routes.handle_register(self, body)

        if path == "/api/triage/analyze":
            return api_routes.handle_triage_analyze(self, body)

        if path == "/api/appointments":
            return api_routes.handle_appointment_book(self, body)

        if path == "/api/referrals/update":
            return api_routes.handle_referral_update(self, body)

        if path == "/api/followups":
            return api_routes.handle_followup_create(self, body)

        if path == "/api/followups/complete":
            return api_routes.handle_followup_complete(self, body)

        self._send_error(404, "Not found")

    # ── OPTIONS (CORS) ──────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── security headers ────────────────────────────────
    def end_headers(self):
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Security-Policy",
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.tailwindcss.com https://cdnjs.cloudflare.com "
            "https://unpkg.com https://ui-avatars.com https://fonts.googleapis.com "
            "https://fonts.gstatic.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org "
            "https://*.basemaps.cartocdn.com https://unpkg.com https://ui-avatars.com; "
            "font-src 'self' https://fonts.gstatic.com;")
        super().end_headers()

    # ── helpers ─────────────────────────────────────────
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status, msg):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def log_message(self, format, *args):
        status = args[1] if len(args) > 1 else ""
        cmd = getattr(self, "command", "UNKNOWN")
        path = getattr(self, "path", "UNKNOWN")
        print(f"  [{cmd}] {path} → {status}")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def _session_cleanup_loop():
    while True:
        time.sleep(3600)
        auth_utils.purge_expired()


if __name__ == "__main__":
    t = threading.Thread(target=_session_cleanup_loop, daemon=True)
    t.start()

    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║   Maharashtra Health Connect — Hacked Build     ║
    ║   Server running at http://localhost:{PORT}        ║
    ║                                                  ║
    ║   → Open http://localhost:{PORT}/final.html        ║
    ║                                                  ║
    ║   ML Model : Disease_symptom_predictor.joblib    ║
    ║   Database : 5589 diseases | 150 facilities      ║
    ║   Symptoms : 30 clinical symptoms                ║
    ║                                                  ║
    ║    2026 The Kacchodis                           ║
    ╚══════════════════════════════════════════════════╝
    """)

    with ReusableTCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
