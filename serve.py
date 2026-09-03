#!/usr/bin/env python3
# ---------------------------------------------------------
# serve.py
# Main Backend Server for Maharashtra Health Connect
# Handles static files, API routes, and Security Integration
# ---------------------------------------------------------

import http.server
import json
import os
import socketserver
import html as html_module
import threading
import time
from urllib.parse import urlparse

# Import our new security module instead of the old auth_utils
import security

PORT = 3000
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

# Load mock hospital data into memory
with open(os.path.join(DIRECTORY, "js", "hospitals-data.json"), "r") as f:
    HOSPITALS = json.load(f)

REVIEWS = {}

class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        # Initialize the static file server
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    # ---------------------------------------------------------
    # GET REQUESTS (Fetching data or HTML pages)
    # ---------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Protect API routes
        if path == "/api/hospitals":
            session = security.validate_session(self)
            if not session:
                self._send_error(401, "Unauthorized")
                return
            self._send_json(HOSPITALS)

        elif path.startswith("/api/hospitals/"):
            session = security.validate_session(self)
            if not session:
                self._send_error(401, "Unauthorized")
                return
            try:
                hid = int(path.split("/")[-1])
                hospital = next((h for h in HOSPITALS if h["id"] == hid), None)
                if hospital:
                    self._send_json(hospital)
                else:
                    self._send_error(404, "Not found")
            except ValueError:
                self._send_error(400, "Bad request")

        elif path.startswith("/api/reviews/"):
            try:
                hid = int(path.split("/")[-1])
                self._send_json(REVIEWS.get(hid, []))
            except ValueError:
                self._send_error(400, "Bad request")

        elif path == "/api/session":
            session = security.validate_session(self)
            self._send_json(security.get_session_info(session))

        elif path == "/api/logout":
            security.destroy_session(self)
            self.send_response(302)
            self.send_header("Set-Cookie", security.build_expire_cookie())
            self.send_header("Location", "/login.html")
            self.end_headers()

        else:
            # Handle standard static files and 404
            
            # Root path redirects to dashboard if authenticated, else login
            if path in ("/", "/index.html"):
                if not security.validate_session(self):
                    self.send_response(302)
                    self.send_header("Location", "/login.html")
                    self.end_headers()
                    return
            
            # Custom 404 Logic
            file_path = os.path.join(DIRECTORY, path.lstrip("/"))
            if path == "/":
                file_path = os.path.join(DIRECTORY, "index.html")
                
            if not os.path.exists(file_path):
                # If file doesn't exist, serve the custom 404.html page
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self._send_security_headers()
                self.end_headers()
                with open(os.path.join(DIRECTORY, "404.html"), "rb") as f:
                    self.wfile.write(f.read())
                return

            super().do_GET()

    def end_headers(self):
        """Override end_headers to automatically inject security headers on every response"""
        self._send_security_headers()
        super().end_headers()

    # ---------------------------------------------------------
    # POST REQUESTS (Login, Register, submitting data)
    # ---------------------------------------------------------
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        if parsed.path == "/api/login":
            client_ip = self.client_address[0]
            if not security.check_rate_limit(client_ip):
                self._send_error(429, "Too many requests. Please try again later.")
                return
                
            try:
                data = json.loads(body)
                username_or_email = data.get("username", "")
                password = data.get("password", "")
                remember = data.get("remember", False)

                # Authenticate via the security module
                username, error = security.authenticate_user(username_or_email, password)
                if error:
                    self._send_error(401, error)
                    return

                sid, ttl = security.create_session(username, remember)
                user = security.USERS[username]

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Set-Cookie", security.build_set_cookie(sid, ttl))
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                }).encode())

            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON")
            except Exception:
                self._send_error(500, "Internal server error")

        elif parsed.path == "/api/register":
            client_ip = self.client_address[0]
            if not security.check_rate_limit(client_ip):
                self._send_error(429, "Too many requests. Please try again later.")
                return
                
            try:
                data = json.loads(body)
                username = data.get("username", "")
                email = data.get("email", "")
                password = data.get("password", "")
                name = data.get("name", "")
                remember = data.get("remember", False)

                # Register via the security module
                username, error = security.register_user(username, email, password, name)
                if error:
                    self._send_error(400, error)
                    return

                sid, ttl = security.create_session(username, remember)

                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.send_header("Set-Cookie", security.build_set_cookie(sid, ttl))
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "name": name.strip(),
                }).encode())

            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON")
            except Exception:
                self._send_error(500, "Internal server error")

        elif parsed.path == "/api/reviews":
            session = security.validate_session(self)
            if not session:
                self._send_error(401, "Unauthorized")
                return
                
            # Example of Role-Based Permission Check
            # Only users (not admins) leave reviews in this system
            # Or you can let anyone do it, but here is the permission hook:
            # if not security.has_permission(session, "user"):
            #     self._send_error(403, "Forbidden")
            #     return
                
            try:
                data = json.loads(body)
                hid = data.get("hospitalId")
                raw_rating = data.get("rating", 3)
                rating = max(1, min(5, int(raw_rating)))
                raw_text = data.get("text", "")
                text = html_module.escape(raw_text[:500])
                review = {
                    "id": len(REVIEWS.get(hid, [])) + 1,
                    "hospitalId": hid,
                    "name": session["name"],
                    "rating": rating,
                    "text": text,
                    "timestamp": data.get("timestamp", ""),
                }
                if hid not in REVIEWS:
                    REVIEWS[hid] = []
                REVIEWS[hid].append(review)
                self._send_json(review, status=201)
            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON")

        else:
            self._send_error(404, "Not found")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ---------------------------------------------------------
    # UTILITY HELPERS
    # ---------------------------------------------------------
    def _send_security_headers(self):
        """Injects strict HTTP Security Headers (Super Security)"""
        # Prevents Clickjacking
        self.send_header("X-Frame-Options", "DENY")
        # Prevents MIME-type sniffing
        self.send_header("X-Content-Type-Options", "nosniff")
        # Enforce HTTPS (Max-Age 1 year)
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        # Basic Content Security Policy
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://unpkg.com https://ui-avatars.com; img-src 'self' data: https://*.tile.openstreetmap.org https://*.basemaps.cartocdn.com https://unpkg.com https://ui-avatars.com;")
        # Enable basic XSS filtering
        self.send_header("X-XSS-Protection", "1; mode=block")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, status, msg):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def log_message(self, fmt, *args):
        # Clean logging format
        method = self.command if hasattr(self, "command") else "-"
        print(f"[{method}] {self.path} -> {args[1] if len(args) > 1 else ''}")


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def _cleanup_expired_sessions():
    """Background thread that cleans up expired sessions from memory."""
    while True:
        time.sleep(3600)
        now = time.time()
        expired = [sid for sid, s in security.SESSIONS.items() if s.get("expires", 0) <= now]
        for sid in expired:
            del security.SESSIONS[sid]

if __name__ == "__main__":
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=_cleanup_expired_sessions, daemon=True)
    cleanup_thread.start()
    
    print(f"""
    ===================================================
      Maharashtra Health Connect
      Server: http://localhost:{PORT}

      Credentials:
        akansh@kacchodis.org / admin123  (Admin)
        demo@kacchodis.org   / demo      (User)
    ===================================================
    """)
    with ReusableTCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
