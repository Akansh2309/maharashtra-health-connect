# data_api.py — ML model + SQLite database + facility routing
# The brain of Maharashtra Health Connect

import json
import os
import html as html_escape_mod
import sqlite3
import warnings
import numpy as np

from config import PUBLIC_DIR, DB_PATH, MODEL_PATH

warnings.filterwarnings("ignore")

# ── Load ML Model at startup ───────────────────────────
import joblib

_ml = joblib.load(MODEL_PATH)
_nn_model = _ml["model"]                    # NearestNeighbors (hamming, k=5)
_symptom_columns = _ml["symptom_columns"]    # 40 symptom names
_disease_names = _ml["disease_names"]        # 5500 disease labels
_training_data = _ml["training_data"]        # 5500x40 binary matrix

print(f"  ✓ ML Model loaded: {len(_symptom_columns)} symptoms → {len(_disease_names.unique())} diseases")

# The 30 real symptoms the user can pick from
SYMPTOM_LIST = [s for s in _symptom_columns if not s.startswith("Symptom_")]

# ── In-memory stores ───────────────────────────────────
_reviews = {}
_referrals = {}
_referral_counter = 1000
_appointments = {}
_appt_counter = 5000
_followups = []


# ── ML Prediction ──────────────────────────────────────

def predict_disease(selected_symptoms):
    """
    Takes a list of symptom names (e.g. ['Fever', 'Cough', 'Headache'])
    Returns top-5 disease predictions with confidence scores.
    """
    # Build binary vector
    vec = np.zeros((1, len(_symptom_columns)), dtype=int)
    for sym in selected_symptoms:
        if sym in _symptom_columns:
            idx = _symptom_columns.index(sym)
            vec[0, idx] = 1

    distances, indices = _nn_model.kneighbors(vec)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        disease = _disease_names.iloc[idx]
        # Hamming distance → confidence (0 distance = 100% match)
        confidence = round((1.0 - dist) * 100, 1)
        results.append({
            "disease": disease,
            "confidence": confidence,
            "distance": round(float(dist), 4)
        })

    return results


# ── Vitals Triage Engine ───────────────────────────────

def triage_vitals(profile, vitals, danger_signs):
    """
    Evaluates patient vitals against clinical thresholds.
    Returns: { is_emergency, triggers[], severity, escalation_action }
    """
    triggers = []
    is_emergency = False

    # Universal danger signs
    if danger_signs.get("bleeding"):
        is_emergency = True
        triggers.append("Heavy Bleeding")
    if danger_signs.get("convulsions"):
        is_emergency = True
        triggers.append("Convulsions/Fits")
    if danger_signs.get("headache"):
        is_emergency = True
        triggers.append("Severe Headache")

    sysBP = vitals.get("sysBP", 0)
    diaBP = vitals.get("diaBP", 0)
    hr = vitals.get("hr", 0)
    temp = vitals.get("temp", 0)

    if profile == "maternal":
        if sysBP >= 160:  triggers.append("Severe Systolic HTN"); is_emergency = True
        if 0 < sysBP <= 80: triggers.append("Hypotension / Shock"); is_emergency = True
        if diaBP >= 110:  triggers.append("Severe Diastolic HTN"); is_emergency = True
        if hr >= 120:     triggers.append("Tachycardia"); is_emergency = True
        if 0 < hr <= 50:  triggers.append("Bradycardia"); is_emergency = True
        if temp >= 38.0:  triggers.append("Fever / Sepsis Risk"); is_emergency = True
    elif profile == "neonate":
        if temp >= 37.5:        triggers.append("Neonatal Fever"); is_emergency = True
        if 0 < temp <= 35.5:    triggers.append("Hypothermia"); is_emergency = True
        if hr > 180:            triggers.append("Tachycardia"); is_emergency = True
        if 0 < hr < 100:       triggers.append("Bradycardia"); is_emergency = True
    elif profile == "child":
        if temp > 38.5:         triggers.append("High Fever"); is_emergency = True
        if 0 < temp <= 35.0:    triggers.append("Hypothermia"); is_emergency = True
        if hr > 150:            triggers.append("Tachycardia"); is_emergency = True
        if 0 < hr < 70:        triggers.append("Bradycardia"); is_emergency = True
        if sysBP >= 120 or (0 < sysBP < 70): triggers.append("Abnormal BP"); is_emergency = True
    else:  # adult
        if sysBP >= 180:        triggers.append("Hypertensive Crisis"); is_emergency = True
        if 0 < sysBP <= 80:    triggers.append("Hypotension / Shock"); is_emergency = True
        if diaBP >= 120:        triggers.append("Diastolic Crisis"); is_emergency = True
        if hr > 130:            triggers.append("Tachycardia"); is_emergency = True
        if 0 < hr < 40:        triggers.append("Bradycardia"); is_emergency = True
        if temp >= 39.0:        triggers.append("High Fever"); is_emergency = True
        if 0 < temp <= 35.0:   triggers.append("Hypothermia"); is_emergency = True

    severity = "CRITICAL" if is_emergency else "STABLE"
    action = "Immediate escalation required" if is_emergency else "Routine care"

    return {
        "is_emergency": is_emergency,
        "triggers": triggers,
        "severity": severity,
        "escalation_action": action
    }


# ── Facility Routing ───────────────────────────────────

def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_facility(specialty=None, emergency=False):
    """Find the best matching facility from 150 hospitals."""
    conn = _get_db()
    cur = conn.cursor()

    if emergency:
        cur.execute("""
            SELECT * FROM facilities
            WHERE emergency_capable = 'Yes' AND doctor_available = 'Yes'
            ORDER BY RANDOM() LIMIT 3
        """)
    elif specialty:
        spec_map = {
            "obstetrics": "Obstetrics", "gynecology": "Obstetrics",
            "pediatrics": "Pediatrics", "neonatology": "Pediatrics",
            "cardiology": "Cardiology", "neurology": "Neurology",
            "orthopedics": "Orthopedics", "general": "General Medicine",
        }
        mapped = spec_map.get(specialty.lower(), "General Medicine")
        cur.execute("""
            SELECT * FROM facilities
            WHERE specialty = ? AND doctor_available = 'Yes'
            ORDER BY RANDOM() LIMIT 3
        """, (mapped,))
    else:
        cur.execute("""
            SELECT * FROM facilities
            WHERE doctor_available = 'Yes'
            ORDER BY RANDOM() LIMIT 3
        """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def search_facilities(query=None, district=None, emergency_only=False):
    """Search all 150 facilities with filters."""
    conn = _get_db()
    cur = conn.cursor()

    sql = "SELECT * FROM facilities WHERE 1=1"
    params = []

    if emergency_only:
        sql += " AND emergency_capable = 'Yes'"
    if district:
        sql += " AND district = ?"
        params.append(district)
    if query:
        sql += " AND (facility_name LIKE ? OR specialty LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])

    sql += " ORDER BY facility_name LIMIT 50"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def search_medicines(query):
    """Search medicine availability across facilities."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT facility_name, district, medicine_name, medicine_in_stock, facility_type
        FROM facilities
        WHERE medicine_name LIKE ? AND medicine_in_stock > 0
        ORDER BY medicine_in_stock DESC LIMIT 20
    """, (f"%{query}%",))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_disease_tests(disease_name):
    """Get recommended diagnostic tests for a disease."""
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT recommended_tests, primary_specialty
        FROM disease_tests
        WHERE disease_name LIKE ? LIMIT 1
    """, (f"%{disease_name}%",))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"tests": dict(row)["recommended_tests"], "specialty": dict(row)["primary_specialty"]}
    return {"tests": "Complete Blood Count (CBC), Basic Metabolic Panel", "specialty": "General Medicine"}


def get_specialty_for_profile(profile, is_emergency):
    """Map patient profile to required specialty."""
    if is_emergency:
        mapping = {
            "maternal": "Obstetrics",
            "neonate": "Pediatrics",
            "child": "Pediatrics",
            "adult": "General Medicine"
        }
    else:
        mapping = {
            "maternal": "Obstetrics",
            "neonate": "Pediatrics",
            "child": "Pediatrics",
            "adult": "General Medicine"
        }
    return mapping.get(profile, "General Medicine")


# ── Symptom Search (HPO DB) ───────────────────────────

def search_symptoms(query, limit=20):
    """Search HPO symptoms from DB."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if not query:
        cur.execute("SELECT hp_id, display_name FROM symptoms LIMIT ?", (limit,))
    else:
        cur.execute("SELECT hp_id, display_name FROM symptoms WHERE display_name LIKE ? LIMIT ?",
                     ('%' + query + '%', limit))
    results = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    conn.close()
    return results


def analyze_symptoms(symptom_ids):
    """Analyze symptoms using the HPO database (legacy endpoint)."""
    if not os.path.exists(DB_PATH) or not symptom_ids:
        return {"diseases": [], "recommended_specialty": None}
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    placeholders = ",".join("?" for _ in symptom_ids)
    query = f'''
        SELECT d.disease_name, ds.disease_id, COUNT(*) as match_count
        FROM disease_symptoms ds
        JOIN diseases d ON ds.disease_id = d.disease_id
        WHERE ds.hp_id IN ({placeholders})
        GROUP BY ds.disease_id
        ORDER BY match_count DESC
        LIMIT 5
    '''
    cur.execute(query, symptom_ids)
    matched = cur.fetchall()
    if not matched:
        conn.close()
        return {"diseases": [], "recommended_specialty": None}
    top_id = matched[0][1]
    cur.execute("SELECT primary_specialty FROM disease_specialties WHERE disease_id = ?", (top_id,))
    spec_row = cur.fetchone()
    specialty = spec_row[0] if spec_row else "General Practice"
    diseases = [{"name": r[0], "matches": r[2]} for r in matched]
    conn.close()
    return {"diseases": diseases, "recommended_specialty": specialty}


# ── Referral Management ────────────────────────────────

def create_referral(patient, triage_result, facility, predicted_disease):
    """Create a digital referral."""
    global _referral_counter
    _referral_counter += 1
    ref_id = f"REF-{_referral_counter}"

    referral = {
        "id": ref_id,
        "patient": patient,
        "status": "CREATED",
        "priority": "EMERGENCY" if triage_result["is_emergency"] else "ROUTINE",
        "facility": facility["facility_name"] if facility else "Nearest PHC",
        "predicted_disease": predicted_disease,
        "triage_triggers": triage_result["triggers"],
        "created_at": __import__("datetime").datetime.now().isoformat(),
        "timeline": [
            {"status": "CREATED", "time": __import__("datetime").datetime.now().isoformat(),
             "note": "Referral created by ASHA worker"}
        ]
    }
    _referrals[ref_id] = referral
    return referral


def get_referral(ref_id):
    return _referrals.get(ref_id)


def update_referral_status(ref_id, new_status, note=""):
    ref = _referrals.get(ref_id)
    if not ref:
        return None
    ref["status"] = new_status
    ref["timeline"].append({
        "status": new_status,
        "time": __import__("datetime").datetime.now().isoformat(),
        "note": note
    })
    return ref


def get_all_referrals():
    return list(_referrals.values())


# ── Appointment Booking ────────────────────────────────

def book_appointment(patient_name, facility_id, specialty, slot):
    global _appt_counter
    _appt_counter += 1
    appt_id = f"APT-{_appt_counter}"

    # Look up facility
    conn = _get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM facilities WHERE facility_id = ?", (facility_id,))
    row = cur.fetchone()
    conn.close()

    facility_name = dict(row)["facility_name"] if row else "Unknown Facility"

    appt = {
        "id": appt_id,
        "patient": patient_name,
        "facility_id": facility_id,
        "facility_name": facility_name,
        "specialty": specialty,
        "slot": slot,
        "status": "CONFIRMED",
        "created_at": __import__("datetime").datetime.now().isoformat()
    }
    _appointments[appt_id] = appt
    return appt


def get_all_appointments():
    return list(_appointments.values())


# ── Follow-up Tasks ────────────────────────────────────

def add_followup(patient_name, task_type, due_date, notes=""):
    task = {
        "id": len(_followups) + 1,
        "patient": patient_name,
        "type": task_type,
        "due_date": due_date,
        "notes": notes,
        "status": "PENDING",
        "created_at": __import__("datetime").datetime.now().isoformat()
    }
    _followups.append(task)
    return task


def get_followups():
    return _followups


def complete_followup(task_id):
    for t in _followups:
        if t["id"] == task_id:
            t["status"] = "COMPLETED"
            return t
    return None


# ── Dashboard Stats ────────────────────────────────────

def get_dashboard_stats():
    """PHC Dashboard summary."""
    total_refs = len(_referrals)
    emergency_refs = sum(1 for r in _referrals.values() if r["priority"] == "EMERGENCY")
    pending_refs = sum(1 for r in _referrals.values() if r["status"] not in ("COMPLETED", "RESOLVED"))
    total_appts = len(_appointments)
    pending_followups = sum(1 for f in _followups if f["status"] == "PENDING")

    return {
        "total_referrals": total_refs,
        "emergency_referrals": emergency_refs,
        "pending_referrals": pending_refs,
        "total_appointments": total_appts,
        "pending_followups": pending_followups,
        "total_facilities": 150,
        "active_asha_workers": 12,
    }
