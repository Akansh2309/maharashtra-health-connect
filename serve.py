#!/usr/bin/env python3
# serve.py — the actual HTTP server
# this file only does routing. all the logic lives in api_routes / auth_utils / data_api

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
        if path == "/api/hospitals":
            return api_routes.handle_hospitals(self)

        if path.startswith("/api/hospitals/"):
            try:
                hid = int(path.split("/")[-1])
            except ValueError:
                return self._send_error(400, "Bad request")
            return api_routes.handle_hospital_detail(self, hid)

        if path.startswith("/api/reviews/"):
            try:
                hid = int(path.split("/")[-1])
            except ValueError:
                return self._send_error(400, "Bad request")
            return api_routes.handle_reviews_get(self, hid)

        if path == "/api/session":
            return api_routes.handle_session(self)

        if path == "/api/logout":
            return api_routes.handle_logout(self)

        # ── static files ────────────────────────────────
        # redirect to login if not authenticated
        if path in ("/", "/index.html"):
            if not auth_utils.get_session(self):
                self.send_response(302)
                self.send_header("Location", "/login.html")
                self.end_headers()
                return

        # custom 404 page
        file_path = os.path.join(PUBLIC_DIR, path.lstrip("/"))
        if path == "/":
            file_path = os.path.join(PUBLIC_DIR, "index.html")

        if not os.path.exists(file_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open(os.path.join(PUBLIC_DIR, "404.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        # let the parent class handle normal file serving
        super().do_GET()

    # ── POST routes ─────────────────────────────────────
    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if path == "/api/login":
            return api_routes.handle_login(self, body)

        if path == "/api/register":
            return api_routes.handle_register(self, body)

        if path == "/api/reviews":
            return api_routes.handle_review_post(self, body)

        self._send_error(404, "Not found")

    # ── OPTIONS (CORS preflight) ────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── security headers on every response ──────────────
    def end_headers(self):
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Strict-Transport-Security",
                         "max-age=31536000; includeSubDomains")
        self.send_header("Content-Security-Policy",
            "default-src 'self' 'unsafe-inline' "
            "https://cdnjs.cloudflare.com https://unpkg.com https://ui-avatars.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org "
            "https://*.basemaps.cartocdn.com https://unpkg.com https://ui-avatars.com;")
        self.send_header("X-XSS-Protection", "1; mode=block")
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

    def log_message(self, fmt, *args):
        # cleaner than the default apache-style log
        status = args[1] if len(args) > 1 else ""
        print(f"  [{self.command}] {self.path} → {status}")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def _session_cleanup_loop():
    # runs every hour in the background, removes expired sessions
    while True:
        time.sleep(3600)
        auth_utils.purge_expired()


if __name__ == "__main__":
    # kick off the session cleanup thread
    t = threading.Thread(target=_session_cleanup_loop, daemon=True)
    t.start()

    print(f"""
    ===================================================
      Maharashtra Health Connect
      Server running at http://localhost:{PORT}

      Login with:
        akansh@kacchodis.org / admin123  (Admin)
        demo@kacchodis.org   / demo      (User)
    ===================================================
    """)

    with ReusableTCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
