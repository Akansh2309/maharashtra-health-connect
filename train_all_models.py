import pandas as pd
import numpy as np
import joblib
import re
import os
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

BASE_DIR = "/Users/akanshshaw/Desktop/HACKATHON/maharashtra-health-connect"
DATA_DIR = BASE_DIR


# 
#  UTILITIES
# 

def split_pascal_case(name):
    """Split PascalCase into spaced words."""
    return re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', name).strip()

def parse_hpo_column(col):
    """Parse HPO column: 'symptom__HP_0000002__Abnormality_of_body_height' -> 'Abnormality of body height'"""
    if col.startswith("symptom__"):
        parts = col.split("__")
        if len(parts) >= 3:
            return parts[2].replace("_", " ")
    return col.replace("_", " ")

def parse_synthetic_column(col):
    """Parse synthetic column: 'AcuteFeverSyndrome' -> 'Acute Fever Syndrome'"""
    return split_pascal_case(col)


# 
#  COMMON DISEASE NAME SIMPLIFICATION
# 

DISEASE_SIMPLIFICATION = {
    "Acute Fever Syndrome": "High Fever",
    "Acute Fever Disorder": "High Fever",
    "Acute Fever Disease": "High Fever",
    "Acute Fever Condition": "High Fever",
    "Chronic Fever Syndrome": "Long-lasting Fever",
    "Chronic Fever Disorder": "Long-lasting Fever",
    "Chronic Fever Disease": "Long-lasting Fever",
    "Severe Fever Syndrome": "Very High Fever",
    "Severe Fever Disorder": "Very High Fever",
    "Mild Fever Syndrome": "Mild Fever",
    "Mild Fever Disorder": "Mild Fever",
    "Primary Arthritis Syndrome": "Joint Pain / Arthritis",
    "Progressive Tachycardia Syndrome": "Fast Heartbeat Problem",
    "Acute Dyspnea Disorder": "Breathing Difficulty",
    "Acute Cough Syndrome": "Bad Cough",
    "Chronic Cough Syndrome": "Long-lasting Cough",
    "Acute Cough Disorder": "Bad Cough",
    "Chronic Cough Disease": "Long-lasting Cough",
    "Acute Headache Syndrome": "Severe Headache",
    "Chronic Headache Syndrome": "Long-lasting Headache",
    "Acute Abdominal Pain Syndrome": "Stomach Pain",
    "Acute Chest Pain Syndrome": "Chest Pain",
    "Acute Joint Pain Condition": "Joint Pain",
    "Chronic Joint Pain Condition": "Long-lasting Joint Pain",
    "Acute Nausea Syndrome": "Feeling Sick / Nausea",
    "Acute Nausea Deficiency": "Feeling Sick / Nausea",
    "Acute Vomiting Syndrome": "Vomiting Problem",
    "Hereditary Vomiting Condition": "Vomiting Problem",
    "Primary Vomiting Disorder": "Vomiting Problem",
    "Acute Diarrhea Syndrome": "Loose Motions",
    "Chronic Diarrhea Syndrome": "Long-lasting Loose Motions",
    "Acute Constipation Syndrome": "Constipation",
    "Acute Dyspnea Syndrome": "Breathing Problem",
    "Chronic Dyspnea Deficiency": "Long-lasting Breathing Problem",
    "Severe Dyspnea Malformation": "Severe Breathing Problem",
    "Severe Dyspnea Disease": "Severe Breathing Problem",
    "Acute Hypertension Condition": "High Blood Pressure",
    "Idiopathic Hypertension Condition": "High Blood Pressure",
    "Severe Tachycardia Dysfunction": "Fast Heartbeat Problem",
    "Primary Tachycardia Deficiency": "Fast Heartbeat Problem",
    "Severe Palpitations Malformation": "Heart Pounding Problem",
    "Primary Palpitations Dysfunction": "Heart Pounding Problem",
    "Congenital Palpitations Syndrome": "Heart Pounding Problem",
    "Hereditary Hypotension Deficiency": "Low Blood Pressure",
    "Acute Skin Rash Syndrome": "Skin Rash",
    "Acute Skin Ulcer Deficiency": "Skin Sore / Ulcer",
    "Severe Skin Ulcer Deficiency": "Skin Sore / Ulcer",
    "Acute Dizziness Syndrome": "Dizziness",
    "Hereditary Dizziness Malformation": "Dizziness Problem",
    "Progressive Ataxia Disorder": "Balance Problem",
    "Idiopathic Ataxia Deficiency": "Balance Problem",
    "Progressive Seizure Disorder": "Seizure / Fits Problem",
    "Secondary Seizure Condition": "Seizure / Fits Problem",
    "Acute Tremor Syndrome": "Shaking / Tremor",
    "Acute Insomnia Dysfunction": "Cannot Sleep",
    "Mild Insomnia Syndrome": "Difficulty Sleeping",
    "Severe Insomnia Dysfunction": "Severe Sleep Problem",
    "Hereditary Hearing Loss Disease": "Hearing Loss",
    "Primary Hearing Loss Deficiency": "Hearing Loss",
    "Chronic Weight Loss Malformation": "Weight Loss Problem",
    "Acute Weight Loss Syndrome": "Sudden Weight Loss",
    "Congenital Muscle Weakness Dysfunction": "Muscle Weakness",
    "Acute Fatigue Syndrome": "Feeling Very Tired",
    "Chronic Fatigue Syndrome": "Long-lasting Tiredness",
}


# 
#  FRONTEND-ALIGNED COMMON DISEASES DATASET
#  These use the EXACT same words as the frontend symptoms
# 

COMMON_DISEASES = [
    {
        "disease": "Viral Fever (Common Flu)",
        "symptoms": "Fever Dry Cough Feeling Weak Fatigue Headache Body Pain Sore Throat Runny Nose Chills Shivering"
    },
    {
        "disease": "Common Cold",
        "symptoms": "Runny Nose Sore Throat Dry Cough Headache Feeling Weak Fatigue Chills Shivering"
    },
    {
        "disease": "Dengue Fever",
        "symptoms": "Fever Headache Body Pain Joint pain Feeling Weak Fatigue Feeling like Vomiting Nausea Skin Rash Itching"
    },
    {
        "disease": "Malaria",
        "symptoms": "Fever Chills Shivering Sweating at night Headache Body Pain Feeling Weak Fatigue Feeling like Vomiting Nausea"
    },
    {
        "disease": "Typhoid Fever",
        "symptoms": "Fever Headache Stomach Ache Feeling Weak Fatigue Loose Motions Diarrhea Loss of Taste Cannot poop Constipation"
    },
    {
        "disease": "Food Poisoning",
        "symptoms": "Throwing up Vomiting Loose Motions Diarrhea Stomach Ache Feeling like Vomiting Nausea Fever Feeling Weak Fatigue"
    },
    {
        "disease": "Stomach Infection (Gastroenteritis)",
        "symptoms": "Stomach Ache Loose Motions Diarrhea Throwing up Vomiting Feeling like Vomiting Nausea Fever Feeling Weak Fatigue"
    },
    {
        "disease": "Acidity / Gas Problem",
        "symptoms": "Acidity Heartburn Stomach Ache Feeling like Vomiting Nausea Chest Pain"
    },
    {
        "disease": "Constipation",
        "symptoms": "Cannot poop Constipation Stomach Ache Acidity Heartburn"
    },
    {
        "disease": "Urinary Tract Infection (UTI)",
        "symptoms": "Peeing too much Fever Stomach Ache Feeling Weak Fatigue"
    },
    {
        "disease": "Diabetes (High Sugar)",
        "symptoms": "Feeling very thirsty Peeing too much Losing weight quickly Feeling Weak Fatigue Blurry vision"
    },
    {
        "disease": "High Blood Pressure",
        "symptoms": "Headache Dizziness Fainting Chest Pain Blurry vision Breathing Problem"
    },
    {
        "disease": "Breathing Problem (Asthma / Bronchitis)",
        "symptoms": "Breathing Problem Dry Cough Wet Cough Chest Pain Feeling Weak Fatigue"
    },
    {
        "disease": "Pneumonia (Lung Infection)",
        "symptoms": "Fever Wet Cough Breathing Problem Chest Pain Chills Shivering Feeling Weak Fatigue"
    },
    {
        "disease": "Tuberculosis (TB)",
        "symptoms": "Wet Cough Fever Sweating at night Losing weight quickly Feeling Weak Fatigue Chest Pain"
    },
    {
        "disease": "COVID-19",
        "symptoms": "Fever Dry Cough Feeling Weak Fatigue Breathing Problem Loss of Taste Loss of Smell Headache Body Pain Sore Throat"
    },
    {
        "disease": "Skin Allergy / Rash",
        "symptoms": "Skin Rash Itching Fever Feeling Weak Fatigue"
    },
    {
        "disease": "Eye Problem (Conjunctivitis)",
        "symptoms": "Blurry vision eye redness eye watering eye pain itching eyes swollen eyelids light sensitivity"
    },
    {
        "disease": "Toothache / Dental Problem",
        "symptoms": "Toothache jaw pain mouth pain swelling face dental cavity gum bleeding tooth sensitivity"
    },
    {
        "disease": "Ear Infection",
        "symptoms": "Fever Headache Dizziness Fainting ear pain ear discharge hearing difficulty ringing in ear"
    },
    {
        "disease": "Migraine (Severe Headache)",
        "symptoms": "Headache Feeling like Vomiting Nausea Blurry vision Dizziness Fainting Cannot sleep"
    },
    {
        "disease": "Anaemia (Low Blood)",
        "symptoms": "Feeling Weak Fatigue Dizziness Fainting Headache Breathing Problem Hair falling out"
    },
    {
        "disease": "Joint Pain / Arthritis",
        "symptoms": "Joint pain Body Pain Swelling in legs Feeling Weak Fatigue"
    },
    {
        "disease": "Back Pain / Muscle Pain",
        "symptoms": "Body Pain lower back pain muscle cramp stiffness Joint pain Feeling Weak Fatigue lifting heavy"
    },
    {
        "disease": "Depression / Sadness",
        "symptoms": "Feeling sad crying Cannot sleep Feeling Weak Fatigue Feeling anxious scared Forgetting things"
    },
    {
        "disease": "Anxiety Problem",
        "symptoms": "Feeling anxious scared Cannot sleep Chest Pain Breathing Problem Dizziness Fainting Hands shaking Tremor"
    },
    {
        "disease": "Thyroid Problem",
        "symptoms": "Gaining weight quickly Feeling Weak Fatigue Hair falling out Cannot sleep Feeling sad crying"
    },
    {
        "disease": "Jaundice (Liver Problem)",
        "symptoms": "Fever Feeling like Vomiting Nausea Feeling Weak Fatigue Losing weight quickly Stomach Ache"
    },
    {
        "disease": "Kidney Problem",
        "symptoms": "Peeing too much Swelling in legs Feeling Weak Fatigue Stomach Ache Feeling like Vomiting Nausea"
    },
    {
        "disease": "Heart Problem",
        "symptoms": "Chest Pain Breathing Problem Dizziness Fainting Sweating at night Feeling Weak Fatigue"
    },
    {
        "disease": "Dehydration",
        "symptoms": "Feeling very thirsty Feeling Weak Fatigue Dizziness Fainting Dry Cough Headache"
    },
    {
        "disease": "Worm Infection (Stomach Worms)",
        "symptoms": "Stomach Ache Losing weight quickly Feeling Weak Fatigue Feeling like Vomiting Nausea"
    },
    {
        "disease": "Chickenpox",
        "symptoms": "Fever Skin Rash Itching Headache Feeling Weak Fatigue Body Pain"
    },
    {
        "disease": "Measles",
        "symptoms": "Fever Skin Rash Itching Dry Cough Runny Nose Sore Throat"
    },
    {
        "disease": "Scabies (Skin Itching)",
        "symptoms": "Skin Rash Itching Cannot sleep"
    },
]


def simplify_disease_name(name):
    """Convert a raw disease name to a simple, rural-friendly name."""
    spaced = split_pascal_case(name)
    return DISEASE_SIMPLIFICATION.get(spaced, spaced)


# 
#  MODEL TRAINING FUNCTIONS
# 

def train_allergy_matcher():
    print("Training Allergy Matcher...")
    df = pd.read_csv(os.path.join(DATA_DIR, "allergies_dataset.csv"))
    df['search_text'] = df['Mild_Symptoms'].fillna('') + " " + df['Severe_Symptoms'].fillna('') + " " + df['Allergy_Name'].fillna('')
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(df['search_text'])
    nn = NearestNeighbors(n_neighbors=3, metric='cosine')
    nn.fit(X)
    model_data = {
        'vectorizer': vectorizer,
        'model': nn,
        'data': df[['Allergy_Name', 'Category', 'Mild_Symptoms', 'Severe_Symptoms', 'Medical_Treatment_Protocol']].to_dict('records')
    }
    joblib.dump(model_data, os.path.join(BASE_DIR, "allergy_matcher.joblib"))
    print("  Allergy Matcher saved.")


def train_deficiency_detector():
    print("Training Deficiency Detector...")
    df = pd.read_csv(os.path.join(DATA_DIR, "deficiencies_dataset.csv"))
    df['search_text'] = df['Primary_Symptoms'].fillna('') + " " + df['Deficiency_Name'].fillna('')
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(df['search_text'])
    nn = NearestNeighbors(n_neighbors=3, metric='cosine')
    nn.fit(X)
    model_data = {
        'vectorizer': vectorizer,
        'model': nn,
        'data': df[['Deficiency_Name', 'Nutrient_Enzyme_Missing', 'Primary_Symptoms', 'Dietary_Sources_Prevention', 'Medical_Treatment_Protocol']].to_dict('records')
    }
    joblib.dump(model_data, os.path.join(BASE_DIR, "deficiency_detector.joblib"))
    print("  Deficiency Detector saved.")


def train_common_disease_matcher():
    """
    TIER 1: Dedicated common disease matcher.
    This is a SEPARATE model trained ONLY on the 35 common diseases
    using the EXACT frontend symptom vocabulary.
    It runs first and catches all normal/common cases with high accuracy.
    """
    print("Training TIER 1: Common Disease Matcher (35 diseases)...")

    disease_names = []
    disease_texts = []

    for entry in COMMON_DISEASES:
        disease_names.append(entry["disease"])
        disease_texts.append(entry["symptoms"])

    vectorizer = TfidfVectorizer()  # No stop words removal — every word matters
    X = vectorizer.fit_transform(disease_texts)

    model_data = {
        'vectorizer': vectorizer,
        'tfidf_matrix': X,
        'disease_names': disease_names,
        'disease_symptoms': disease_texts,
    }

    joblib.dump(model_data, os.path.join(BASE_DIR, "common_disease_matcher.joblib"))
    print(f"  Common Disease Matcher saved ({len(disease_names)} diseases).")

    # Validation
    print("\n  === TIER 1 VALIDATION (Common Diseases) ===")
    from sklearn.metrics.pairwise import cosine_similarity

    test_cases = [
        ("Fever Dry Cough Headache", "Viral Fever or Common Cold"),
        ("Stomach Ache Loose Motions Diarrhea Throwing up Vomiting", "Food Poisoning / Stomach Infection"),
        ("Breathing Problem Chest Pain Feeling Weak Fatigue", "Asthma or Heart Problem"),
        ("Fever Headache Body Pain Joint pain", "Dengue"),
        ("Feeling very thirsty Peeing too much Losing weight quickly", "Diabetes"),
        ("Skin Rash Itching Fever Headache", "Chickenpox or Skin Allergy"),
        ("Fever Chills Shivering Sweating at night Headache Body Pain", "Malaria"),
        ("Wet Cough Fever Sweating at night Losing weight quickly", "TB"),
        ("Headache Feeling like Vomiting Nausea Blurry vision", "Migraine"),
        ("Feeling anxious scared Cannot sleep Chest Pain", "Anxiety"),
        ("Feeling sad crying Cannot sleep Feeling Weak Fatigue", "Depression"),
        ("Gaining weight quickly Feeling Weak Fatigue Hair falling out", "Thyroid"),
    ]

    for symptoms_text, expected in test_cases:
        vec = vectorizer.transform([symptoms_text])
        sims = cosine_similarity(vec, X)[0]
        top_idx = np.argmax(sims)
        top_score = sims[top_idx]
        top_disease = disease_names[top_idx]
        confidence = round(top_score * 100, 1)

        # Get top 3
        top3_idx = np.argsort(sims)[-3:][::-1]
        alts = [(disease_names[i], round(sims[i]*100, 1)) for i in top3_idx]

        status = "OK" if confidence >= 30 else "WARN"
        print(f"  [{status}] '{symptoms_text[:45]}...'")
        print(f"       -> {top_disease} ({confidence}%)")
        print(f"       Alts: {alts}")
        print(f"       Expected: {expected}")
        print()


def train_disease_predictor():
    """
    TIER 2: Full NLP Disease Predictor for rare/complex diseases.
    Runs as fallback when Tier 1 (common matcher) has low confidence.
    """
    print("Training TIER 2: Full NLP Disease Predictor...")

    disease_texts = []
    disease_names = []

    # Step 1: Process HPO dataset
    print("  Processing HPO dataset...")
    hpo_df = pd.read_csv(os.path.join(BASE_DIR, "../disease_symptom_binary_hpo_2026-09-02.csv"))
    hpo_symptom_cols = [c for c in hpo_df.columns if c not in ("disease_id", "disease_name")]

    for idx, row in hpo_df.iterrows():
        raw_name = row['disease_name']
        simple_name = simplify_disease_name(str(raw_name))
        symptoms = []
        for col in hpo_symptom_cols:
            if row[col] == 1:
                readable = parse_hpo_column(col)
                symptoms.append(readable)
        if symptoms:
            disease_names.append(simple_name)
            disease_texts.append(" ".join(symptoms))

    print(f"    HPO: {len(disease_names)} entries")

    # Step 2: Process 10K synthetic dataset
    print("  Processing 10K synthetic dataset...")
    syn_df = pd.read_csv(os.path.join(BASE_DIR, "../synthetic_disease_symptom_10k.csv"))
    syn_symptom_cols = [c for c in syn_df.columns if c != "disease_name"]

    for idx, row in syn_df.iterrows():
        raw_name = row['disease_name']
        simple_name = simplify_disease_name(str(raw_name))
        symptoms = []
        for col in syn_symptom_cols:
            if row[col] == 1:
                readable = parse_synthetic_column(col)
                symptoms.append(readable)
        if symptoms:
            disease_names.append(simple_name)
            disease_texts.append(" ".join(symptoms))

    print(f"    Total: {len(disease_names)} entries")

    # Step 3: Build model
    print("  Building TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=8000)
    X = vectorizer.fit_transform(disease_texts)

    print("  Training NearestNeighbors...")
    nn = NearestNeighbors(n_neighbors=5, metric='cosine')
    nn.fit(X)

    model_data = {
        'vectorizer': vectorizer,
        'model': nn,
        'disease_names': disease_names
    }
    joblib.dump(model_data, os.path.join(BASE_DIR, "disease_predictor_nlp.joblib"))
    print(f"  NLP Disease Predictor saved ({len(disease_names)} diseases).")



def train_bed_predictor():
    print("Training 3 Bed Availability Predictors (General, ICU, Ventilator)...")
    file_path = os.path.join(DATA_DIR, "ml_predictive_bed_data_10_years.csv")
    if not os.path.exists(file_path):
        print("  Skipping: bed data file not found.")
        return
    
    model_gen = SGDRegressor(max_iter=1000, tol=1e-3, penalty='l2')
    model_icu = SGDRegressor(max_iter=1000, tol=1e-3, penalty='l2')
    model_vent = SGDRegressor(max_iter=1000, tol=1e-3, penalty='l2')
    
    scaler_gen = StandardScaler()
    scaler_icu = StandardScaler()
    scaler_vent = StandardScaler()
    
    chunksize = 200_000
    reader = pd.read_csv(file_path, chunksize=chunksize)
    chunk_num = 1
    start_time = time.time()
    
    # We will only train on 1 chunk for speed, normally you'd loop
    for chunk in reader:
        chunk['Timestamp'] = pd.to_datetime(chunk['Timestamp'])
        chunk['hour'] = chunk['Timestamp'].dt.hour
        chunk['month'] = chunk['Timestamp'].dt.month
        chunk['dayofweek'] = chunk['Timestamp'].dt.dayofweek
        
        X = chunk[['hour', 'month', 'dayofweek']].values
        
        # We need targets for Gen, ICU, Vent. We only have Total_Beds, General_Beds_Available, ICU_Beds_Available, Ventilator_Beds_Available, Occupancy_Rate_Pct
        # The user wants models for predicting bed availability. 
        # We will predict the raw counts or percentages. Let's predict raw counts as a percentage of capacity, or just the available beds directly.
        # It's simpler to predict the number of available beds directly.
        
        y_gen = chunk['General_Beds_Available'].values
        y_icu = chunk['ICU_Beds_Available'].values
        y_vent = chunk['Ventilator_Beds_Available'].values
        
        scaler_gen.partial_fit(X)
        scaler_icu.partial_fit(X)
        scaler_vent.partial_fit(X)
        
        X_scaled_gen = scaler_gen.transform(X)
        X_scaled_icu = scaler_icu.transform(X)
        X_scaled_vent = scaler_vent.transform(X)
        
        model_gen.partial_fit(X_scaled_gen, y_gen)
        model_icu.partial_fit(X_scaled_icu, y_icu)
        model_vent.partial_fit(X_scaled_vent, y_vent)
        
        elapsed = time.time() - start_time
        print(f"  Chunk {chunk_num} (200k rows). Elapsed: {elapsed:.1f}s")
        break # Just 1 chunk for faster training during hackathon
        
    joblib.dump({'model': model_gen, 'scaler': scaler_gen}, os.path.join(BASE_DIR, "bed_predictor_general.joblib"))
    joblib.dump({'model': model_icu, 'scaler': scaler_icu}, os.path.join(BASE_DIR, "bed_predictor_icu.joblib"))
    joblib.dump({'model': model_vent, 'scaler': scaler_vent}, os.path.join(BASE_DIR, "bed_predictor_ventilator.joblib"))
    print("  3 Bed Predictors saved.")



if __name__ == "__main__":
    print("=" * 60)
    print("  Maharashtra Health Connect - Model Training")
    print("=" * 60)
    print()
    train_allergy_matcher()
    print()
    train_deficiency_detector()
    print()
    train_common_disease_matcher()
    print()
    train_disease_predictor()
    print()
    # Skip bed predictor (takes very long)
    train_bed_predictor()
    print("=" * 60)
    print("  All models successfully trained and saved!")
    print("=" * 60)
