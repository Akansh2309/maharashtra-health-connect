# api_routes.py — one function per API endpoint
# the server just calls the right function here based on the URL

import json
import auth_utils
import data_api


# ── auth endpoints ──────────────────────────────────────

def handle_login(server, body):
    ip = server.client_address[0]
    if not auth_utils.rate_limit_ok(ip):
        return server._send_error(429, "Too many attempts, slow down a bit")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")

    login_id = data.get("username", "")
    password = data.get("password", "")
    remember = data.get("remember", False)

    if not login_id or not password:
        return server._send_error(400, "Username and password required")

    username, err = auth_utils.authenticate(login_id, password)
    if err:
        return server._send_error(401, err)

    # all good — create session and send cookie
    sid, ttl = auth_utils.create_session(username, remember)
    user = auth_utils.USERS[username]

    server.send_response(200)
    server.send_header("Content-Type", "application/json")
    server.send_header("Set-Cookie", auth_utils.make_cookie(sid, ttl))
    server.end_headers()
    server.wfile.write(json.dumps({
        "success": True,
        "name": user["name"],
        "email": user.get("email", ""),
        "role": user["role"],
    }).encode())


def handle_register(server, body):
    ip = server.client_address[0]
    if not auth_utils.rate_limit_ok(ip):
        return server._send_error(429, "Too many attempts, try again later")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")

    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")
    name = data.get("name", "")
    remember = data.get("remember", False)

    username, err = auth_utils.register(username, email, password, name)
    if err:
        return server._send_error(400, err)

    sid, ttl = auth_utils.create_session(username, remember)

    server.send_response(201)
    server.send_header("Content-Type", "application/json")
    server.send_header("Set-Cookie", auth_utils.make_cookie(sid, ttl))
    server.end_headers()
    server.wfile.write(json.dumps({
        "success": True,
        "name": name.strip(),
    }).encode())


def handle_session(server):
    sess = auth_utils.get_session(server)
    return server._send_json(auth_utils.session_info(sess))


def handle_logout(server):
    auth_utils.kill_session(server)
    server.send_response(302)
    server.send_header("Set-Cookie", auth_utils.expire_cookie())
    server.send_header("Location", "/login.html")
    server.end_headers()


# ── hospital data endpoints ─────────────────────────────

def handle_hospitals(server):
    # need to be logged in to see hospital data
    sess = auth_utils.get_session(server)
    if not sess:
        return server._send_error(401, "Unauthorized")
    return server._send_json(data_api.get_all_hospitals())


def handle_hospital_detail(server, hospital_id):
    sess = auth_utils.get_session(server)
    if not sess:
        return server._send_error(401, "Unauthorized")

    hospital = data_api.get_hospital_by_id(hospital_id)
    if not hospital:
        return server._send_error(404, "Hospital not found")
    return server._send_json(hospital)


# ── review endpoints ────────────────────────────────────

def handle_reviews_get(server, hospital_id):
    # reviews are public — no auth needed
    return server._send_json(data_api.get_reviews(hospital_id))


def handle_review_post(server, body):
    sess = auth_utils.get_session(server)
    if not sess:
        return server._send_error(401, "You need to be logged in to leave a review")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")

    hid = data.get("hospitalId")
    rating = data.get("rating", 3)
    text = data.get("text", "")

    try:
        review = data_api.add_review(hid, sess, rating, text)
    except LookupError as e:
        return server._send_error(404, str(e))
    except ValueError as e:
        return server._send_error(400, str(e))

    return server._send_json(review, status=201)

# ── triage endpoints ────────────────────────────────────

def handle_symptoms_search(server, query_params):
    # Public endpoint
    query = ""
    # Very basic parsing since we only use basic python http.server
    if "?q=" in server.path:
        query = server.path.split("?q=")[1].split("&")[0]
        # urldecode it
        from urllib.parse import unquote
        query = unquote(query)
        
    symptoms = data_api.search_symptoms(query)
    return server._send_json(symptoms)

def handle_triage_analyze(server, body):
    # ASHA worker must be logged in ideally, but let's keep it simple for MVP
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")
        
    symptom_ids = data.get("symptoms", [])
    if not isinstance(symptom_ids, list):
        return server._send_error(400, "Symptoms must be a list of IDs")
        
    result = data_api.analyze_symptoms(symptom_ids)
    return server._send_json(result)
