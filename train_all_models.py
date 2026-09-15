import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler
import time
import os

BASE_DIR = "/Users/akanshshaw/Desktop/HACKATHON/maharashtra-health-connect"
DATA_DIR = BASE_DIR

def train_allergy_matcher():
    print("Training Allergy Matcher...")
    df = pd.read_csv(os.path.join(DATA_DIR, "allergies_dataset.csv"))
    
    # Combine relevant text for matching
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
    print("Allergy Matcher saved.")

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
    print("Deficiency Detector saved.")

def train_disease_predictor():
    print("Training NLP Disease Predictor (15,500+ diseases)...")
    
    # Load 5.5K HPO dataset
    hpo_df = pd.read_csv(os.path.join(BASE_DIR, "../disease_symptom_binary_hpo_2026-09-02.csv"))
    disease_texts = []
    disease_names = []
    
    symptom_cols = hpo_df.columns[1:]
    
    print("Processing HPO dataset...")
    for idx, row in hpo_df.iterrows():
        name = row['disease_name']
        symptoms = [str(col) for col, val in zip(symptom_cols, row[1:]) if val == 1]
        disease_names.append(name)
        disease_texts.append(" ".join(symptoms))
        
    print("Processing 10K dataset...")
    syn_df = pd.read_csv(os.path.join(BASE_DIR, "../synthetic_disease_symptom_10k.csv"))
    syn_symptom_cols = syn_df.columns[1:]
    
    for idx, row in syn_df.iterrows():
        name = row['disease_name']
        symptoms = [str(col) for col, val in zip(syn_symptom_cols, row[1:]) if val == 1]
        disease_names.append(name)
        disease_texts.append(" ".join(symptoms))
        
    print(f"Total diseases: {len(disease_names)}")
    
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    X = vectorizer.fit_transform(disease_texts)
    
    nn = NearestNeighbors(n_neighbors=5, metric='cosine')
    nn.fit(X)
    
    model_data = {
        'vectorizer': vectorizer,
        'model': nn,
        'disease_names': disease_names
    }
    joblib.dump(model_data, os.path.join(BASE_DIR, "disease_predictor_nlp.joblib"))
    print("NLP Disease Predictor saved.")

def train_bed_predictor():
    print("Training Bed Availability Predictor on full 33 Million rows...")
    file_path = os.path.join(DATA_DIR, "ml_predictive_bed_data_10_years.csv")
    
    model = SGDRegressor(max_iter=1000, tol=1e-3, penalty='l2')
    scaler = StandardScaler()
    
    chunksize = 1_000_000
    reader = pd.read_csv(file_path, chunksize=chunksize)
    
    chunk_num = 1
    start_time = time.time()
    
    for chunk in reader:
        chunk['Timestamp'] = pd.to_datetime(chunk['Timestamp'])
        chunk['hour'] = chunk['Timestamp'].dt.hour
        chunk['month'] = chunk['Timestamp'].dt.month
        chunk['dayofweek'] = chunk['Timestamp'].dt.dayofweek
        
        X = chunk[['hour', 'month', 'dayofweek']].values
        y = chunk['Occupancy_Rate_Pct'].values
        
        scaler.partial_fit(X)
        X_scaled = scaler.transform(X)
        
        model.partial_fit(X_scaled, y)
        
        elapsed = time.time() - start_time
        print(f"Processed chunk {chunk_num} (1M rows). Elapsed: {elapsed:.1f}s")
        chunk_num += 1
        
    joblib.dump({'model': model, 'scaler': scaler}, os.path.join(BASE_DIR, "bed_predictor.joblib"))
    print("Bed Predictor saved.")

if __name__ == "__main__":
    train_allergy_matcher()
    train_deficiency_detector()
    train_disease_predictor()
    train_bed_predictor()
    print("All models successfully trained and saved!")
