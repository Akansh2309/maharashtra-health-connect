# data_api.py — loads the hospital dataset and manages reviews
# keeps all the "data stuff" out of the server file

import json
import os
import html as html_escape_mod

from config import PUBLIC_DIR

# ── load hospital data once at startup ──────────────────
_data_path = os.path.join(PUBLIC_DIR, "js", "hospitals-data.json")

with open(_data_path, "r") as _f:
    _hospitals = json.load(_f)

# reviews are stored in memory — keyed by hospital id
# in a real app this would be a database table obviously
_reviews = {}


def get_all_hospitals():
    return _hospitals


def get_hospital_by_id(hid):
    # linear scan is fine for 65 records, no need to overthink it
    for h in _hospitals:
        if h["id"] == hid:
            return h
    return None


def get_reviews(hospital_id):
    return _reviews.get(hospital_id, [])


def add_review(hospital_id, session, rating, text):
    """
    Adds a review for a hospital. Validates the rating range and
    sanitises the text so nobody injects HTML into our page.
    Returns the new review dict, or raises ValueError/LookupError.
    """
    # make sure the hospital actually exists
    if get_hospital_by_id(hospital_id) is None:
        raise LookupError("Hospital not found")

    # clamp rating to 1-5
    try:
        rating = max(1, min(5, int(rating)))
    except (TypeError, ValueError):
        raise ValueError("Rating must be a number between 1 and 5")

    # sanitise review text — strip html tags, cap at 500 chars
    clean_text = html_escape_mod.escape(str(text)[:500])

    # build the review object
    existing = _reviews.get(hospital_id, [])
    review = {
        "id": len(existing) + 1,
        "hospitalId": hospital_id,
        "name": session["name"],
        "rating": rating,
        "text": clean_text,
    }

    if hospital_id not in _reviews:
        _reviews[hospital_id] = []
    _reviews[hospital_id].append(review)

    return review

import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "hpo_database.db")

def search_symptoms(query, limit=20):
    if not os.path.exists(DB_PATH):
        return []
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    if not query:
        # Return 20 random or common ones
        cur.execute("SELECT hp_id, display_name FROM symptoms LIMIT ?", (limit,))
    else:
        cur.execute("SELECT hp_id, display_name FROM symptoms WHERE display_name LIKE ? LIMIT ?", ('%' + query + '%', limit))
        
    results = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    conn.close()
    return results

def analyze_symptoms(symptom_ids):
    if not os.path.exists(DB_PATH) or not symptom_ids:
        return {"diseases": [], "recommended_specialty": None}
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # We want to find diseases that have the MOST matches with the given symptom IDs
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
    matched_diseases = cur.fetchall()
    
    if not matched_diseases:
        conn.close()
        return {"diseases": [], "recommended_specialty": None}
        
    # Get the specialty for the top matched disease
    top_disease_id = matched_diseases[0][1]
    cur.execute("SELECT primary_specialty FROM disease_specialties WHERE disease_id = ?", (top_disease_id,))
    spec_row = cur.fetchone()
    primary_specialty = spec_row[0] if spec_row else "General Practice"
    
    # In the dataset, specialties look like "Neurology", "Clinical Genetics", "Cardiology"
    # Our hospital DB uses "neurology", "cardiology", "pediatrics", "maternity"
    # We can do a simple mapping for the MVP
    spec_lower = primary_specialty.lower()
    if "cardio" in spec_lower:
        mapped_specialty = "cardiology"
    elif "pediatric" in spec_lower:
        mapped_specialty = "pediatrics"
    elif "obstetrics" in spec_lower or "gynecol" in spec_lower or "matern" in spec_lower:
        mapped_specialty = "maternity"
    elif "neurol" in spec_lower:
        mapped_specialty = "neurology"
    elif "ortho" in spec_lower:
        mapped_specialty = "orthopedics"
    elif "oncol" in spec_lower:
        mapped_specialty = "oncology"
    else:
        mapped_specialty = "general"
        
    diseases = [{"name": r[0], "matches": r[2]} for r in matched_diseases]
    
    conn.close()
    return {
        "diseases": diseases,
        "recommended_specialty": mapped_specialty,
        "raw_specialty": primary_specialty
    }
