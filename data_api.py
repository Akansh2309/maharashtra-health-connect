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
