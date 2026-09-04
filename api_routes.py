# api_routes.py — one function per API endpoint
# Enhanced for the Hacked build with ML, referrals, appointments, etc.

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
    sid, ttl = auth_utils.create_session(username, remember)
    user = auth_utils.USERS[username]
    server.send_response(200)
    server.send_header("Content-Type", "application/json")
    server.send_header("Set-Cookie", auth_utils.make_cookie(sid, ttl))
    server.end_headers()
    server.wfile.write(json.dumps({
        "success": True, "name": user["name"],
        "email": user.get("email", ""), "role": user["role"],
    }).encode())


def handle_register(server, body):
    ip = server.client_address[0]
    if not auth_utils.rate_limit_ok(ip):
        return server._send_error(429, "Too many attempts")
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
    server.wfile.write(json.dumps({"success": True, "name": name.strip()}).encode())


def handle_session(server):
    sess = auth_utils.get_session(server)
    return server._send_json(auth_utils.session_info(sess))


def handle_logout(server):
    auth_utils.kill_session(server)
    server.send_response(302)
    server.send_header("Set-Cookie", auth_utils.expire_cookie())
    server.send_header("Location", "/login.html")
    server.end_headers()


# ── ML Prediction + Triage (THE MAIN ENDPOINT) ─────────

def handle_predict(server, body):
    """
    POST /api/predict
    Body: { profile, symptoms[], vitals: {sysBP, diaBP, hr, temp},
            danger_signs: {bleeding, convulsions, headache},
            patient: {name, age, village} }
    Returns: ML prediction + triage + facility + referral
    """
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")

    profile = data.get("profile", "adult")
    symptoms = data.get("symptoms", [])
    vitals = data.get("vitals", {})
    danger_signs = data.get("danger_signs", {})
    patient = data.get("patient", {})

    # 1. ML Disease Prediction
    predictions = data_api.predict_disease(symptoms)
    top_disease = predictions[0]["disease"] if predictions else "Unknown"
    top_confidence = predictions[0]["confidence"] if predictions else 0

    # 2. Vitals Triage
    triage = data_api.triage_vitals(profile, vitals, danger_signs)

    # 3. Get diagnostic tests for predicted disease
    tests_info = data_api.get_disease_tests(top_disease)

    # 4. Find appropriate facility
    specialty = tests_info.get("specialty", "General Medicine")
    facilities = data_api.find_facility(
        specialty=specialty,
        emergency=triage["is_emergency"]
    )
    primary_facility = facilities[0] if facilities else None

    # 5. Auto-create referral if emergency
    referral = None
    if triage["is_emergency"] and patient.get("name"):
        referral = data_api.create_referral(patient, triage, primary_facility, top_disease)
        # Auto-create follow-up task
        import datetime
        due = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        data_api.add_followup(
            patient.get("name", "Unknown"),
            "Post-Emergency Follow-up",
            due,
            f"Follow up after {top_disease} emergency"
        )

    response = {
        "prediction": {
            "top_disease": top_disease,
            "confidence": top_confidence,
            "alternatives": predictions[1:4] if len(predictions) > 1 else [],
            "symptoms_analyzed": len(symptoms),
        },
        "triage": triage,
        "diagnostics": {
            "recommended_tests": tests_info["tests"],
            "specialty": tests_info["specialty"],
        },
        "facility": primary_facility,
        "all_facilities": facilities,
        "referral": referral,
    }

    return server._send_json(response)


# ── Symptom List ────────────────────────────────────────

def handle_symptom_list(server):
    """GET /api/symptoms — returns the 30 real symptoms the ML model knows."""
    return server._send_json({"symptoms": data_api.SYMPTOM_LIST})


def handle_symptoms_search(server, query_params):
    query = ""
    if "?q=" in server.path:
        from urllib.parse import unquote
        query = unquote(server.path.split("?q=")[1].split("&")[0])
    symptoms = data_api.search_symptoms(query)
    return server._send_json(symptoms)


def handle_triage_analyze(server, body):
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")
    symptom_ids = data.get("symptoms", [])
    if not isinstance(symptom_ids, list):
        return server._send_error(400, "Symptoms must be a list of IDs")
    result = data_api.analyze_symptoms(symptom_ids)
    return server._send_json(result)


# ── Facility Endpoints ─────────────────────────────────

def handle_facilities(server):
    """GET /api/facilities — all 150 facilities."""
    facilities = data_api.search_facilities()
    return server._send_json(facilities)


def handle_facilities_search(server):
    """GET /api/facilities/search?q=&district=&emergency="""
    from urllib.parse import urlparse, parse_qs
    params = parse_qs(urlparse(server.path).query)
    query = params.get("q", [""])[0]
    district = params.get("district", [""])[0] or None
    emergency = params.get("emergency", [""])[0] == "true"
    results = data_api.search_facilities(query, district, emergency)
    return server._send_json(results)


# ── Medicine Lookup ────────────────────────────────────

def handle_medicines_search(server):
    """GET /api/medicines/search?q=paracetamol"""
    from urllib.parse import urlparse, parse_qs
    params = parse_qs(urlparse(server.path).query)
    query = params.get("q", [""])[0]
    if not query:
        return server._send_json([])
    results = data_api.search_medicines(query)
    return server._send_json(results)


# ── Referral Endpoints ─────────────────────────────────

def handle_referrals_get(server):
    """GET /api/referrals"""
    return server._send_json(data_api.get_all_referrals())


def handle_referral_detail(server, ref_id):
    """GET /api/referrals/<id>"""
    ref = data_api.get_referral(ref_id)
    if not ref:
        return server._send_error(404, "Referral not found")
    return server._send_json(ref)


def handle_referral_update(server, body):
    """POST /api/referrals/update"""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")
    ref_id = data.get("id")
    status = data.get("status", "IN_PROGRESS")
    note = data.get("note", "")
    ref = data_api.update_referral_status(ref_id, status, note)
    if not ref:
        return server._send_error(404, "Referral not found")
    return server._send_json(ref)


# ── Appointment Endpoints ──────────────────────────────

def handle_appointment_book(server, body):
    """POST /api/appointments"""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")
    patient = data.get("patient_name", "Unknown")
    facility_id = data.get("facility_id", "FAC0001")
    specialty = data.get("specialty", "General Medicine")
    slot = data.get("slot", "Next Available")
    appt = data_api.book_appointment(patient, facility_id, specialty, slot)
    return server._send_json(appt, status=201)


def handle_appointments_get(server):
    """GET /api/appointments"""
    return server._send_json(data_api.get_all_appointments())


# ── Follow-up Endpoints ───────────────────────────────

def handle_followups_get(server):
    """GET /api/followups"""
    return server._send_json(data_api.get_followups())


def handle_followup_create(server, body):
    """POST /api/followups"""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")
    task = data_api.add_followup(
        data.get("patient", "Unknown"),
        data.get("type", "General Follow-up"),
        data.get("due_date", ""),
        data.get("notes", "")
    )
    return server._send_json(task, status=201)


def handle_followup_complete(server, body):
    """POST /api/followups/complete"""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return server._send_error(400, "Invalid JSON")
    task = data_api.complete_followup(data.get("id"))
    if not task:
        return server._send_error(404, "Task not found")
    return server._send_json(task)


# ── Dashboard ──────────────────────────────────────────

def handle_dashboard(server):
    """GET /api/dashboard"""
    return server._send_json(data_api.get_dashboard_stats())
