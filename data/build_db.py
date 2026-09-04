import sqlite3
import csv
import os

DB_PATH = 'hpo_database.db'
SYMPTOMS_CSV = 'disease_symptom_binary_hpo_2026-09-02.csv'
MAPPING_CSV = 'disease_specialist_referral_mapping_hpo_2026-09-02.csv'
FACILITIES_CSV = 'facility_availability.csv'
VITALS_CSV = 'clinical_vitals_thresholds.csv'
TESTS_CSV = 'disease_diagnostic_tests.csv'

def clean_symptom_name(raw_col):
    parts = raw_col.split('__')
    if len(parts) >= 3:
        hp_id = parts[1]
        name = parts[2].replace('_', ' ')
        return hp_id, name
    return None, raw_col

def build_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE diseases (
            disease_id TEXT PRIMARY KEY,
            disease_name TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE symptoms (
            hp_id TEXT PRIMARY KEY,
            display_name TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE disease_symptoms (
            disease_id TEXT,
            hp_id TEXT,
            FOREIGN KEY(disease_id) REFERENCES diseases(disease_id),
            FOREIGN KEY(hp_id) REFERENCES symptoms(hp_id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE disease_specialties (
            disease_id TEXT PRIMARY KEY,
            primary_specialty TEXT,
            routing_confidence TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE facilities (
            facility_id TEXT PRIMARY KEY,
            facility_name TEXT,
            district TEXT,
            village_or_pincode TEXT,
            facility_type TEXT,
            specialty TEXT,
            doctor_available TEXT,
            teleconsultation_available TEXT,
            next_slot TEXT,
            diagnostic_test_available TEXT,
            medicine_name TEXT,
            medicine_in_stock INTEGER,
            emergency_capable TEXT,
            operating_hours TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE clinical_vitals (
            rule_id TEXT PRIMARY KEY,
            patient_profile TEXT,
            vital_parameter TEXT,
            safe_min TEXT,
            safe_max TEXT,
            critical_min TEXT,
            critical_max TEXT,
            observational_sign TEXT,
            escalation_action TEXT,
            source TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE disease_tests (
            disease_id TEXT PRIMARY KEY,
            disease_name TEXT,
            primary_specialty TEXT,
            recommended_tests TEXT,
            FOREIGN KEY(disease_id) REFERENCES diseases(disease_id)
        )
    ''')
    
    cur.execute('CREATE INDEX idx_disease_symptoms_hp_id ON disease_symptoms(hp_id)')
    cur.execute('CREATE INDEX idx_disease_symptoms_disease_id ON disease_symptoms(disease_id)')
    cur.execute('CREATE INDEX idx_symptoms_name ON symptoms(display_name COLLATE NOCASE)')
    cur.execute('CREATE INDEX idx_facilities_specialty ON facilities(specialty)')
    cur.execute('CREATE INDEX idx_facilities_district ON facilities(district)')
    
    print("Ingesting symptoms matrix (this may take a minute)...")
    with open(SYMPTOMS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        symptom_cols = []
        for i, col in enumerate(headers[2:]):
            hp_id, display_name = clean_symptom_name(col)
            if hp_id:
                cur.execute('INSERT OR IGNORE INTO symptoms (hp_id, display_name) VALUES (?, ?)', (hp_id, display_name))
                symptom_cols.append((i+2, hp_id))
        
        for row in reader:
            if not row: continue
            d_id = row[0]
            d_name = row[1]
            cur.execute('INSERT OR IGNORE INTO diseases (disease_id, disease_name) VALUES (?, ?)', (d_id, d_name))
            
            for col_idx, hp_id in symptom_cols:
                if col_idx < len(row) and row[col_idx] == '1':
                    cur.execute('INSERT INTO disease_symptoms (disease_id, hp_id) VALUES (?, ?)', (d_id, hp_id))
                    
    print("Ingesting specialist mapping...")
    with open(MAPPING_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_id = row.get('disease_id')
            spec = row.get('primary_specialty')
            conf = row.get('routing_confidence')
            if d_id and spec:
                cur.execute('''
                    INSERT OR REPLACE INTO disease_specialties (disease_id, primary_specialty, routing_confidence) 
                    VALUES (?, ?, ?)
                ''', (d_id, spec, conf))
                
    print("Ingesting facility availability data...")
    if os.path.exists(FACILITIES_CSV):
        with open(FACILITIES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute('''
                    INSERT OR REPLACE INTO facilities (
                        facility_id, facility_name, district, village_or_pincode, facility_type, 
                        specialty, doctor_available, teleconsultation_available, next_slot, 
                        diagnostic_test_available, medicine_name, medicine_in_stock, emergency_capable, operating_hours
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('facility_id'), row.get('facility_name'), row.get('district'), 
                    row.get('village_or_pincode'), row.get('facility_type'), row.get('specialty'), 
                    row.get('doctor_available'), row.get('teleconsultation_available'), row.get('next_slot'), 
                    row.get('diagnostic_test_available'), row.get('medicine_name'), 
                    int(row.get('medicine_in_stock', 0)), row.get('emergency_capable'), row.get('operating_hours')
                ))
    else:
        print(f"Warning: {FACILITIES_CSV} not found. Skipping facilities ingestion.")

    print("Ingesting clinical vitals rules...")
    if os.path.exists(VITALS_CSV):
        with open(VITALS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cur.execute('''
                    INSERT OR REPLACE INTO clinical_vitals (
                        rule_id, patient_profile, vital_parameter, 
                        safe_min, safe_max, critical_min, critical_max, 
                        observational_sign, escalation_action, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('rule_id'), row.get('patient_profile'), row.get('vital_parameter'),
                    row.get('safe_min'), row.get('safe_max'), row.get('critical_min'), row.get('critical_max'),
                    row.get('observational_sign'), row.get('escalation_action'), row.get('source')
                ))
    else:
        print(f"Warning: {VITALS_CSV} not found. Skipping clinical vitals ingestion.")

    print("Ingesting disease diagnostic tests mapping...")
    if os.path.exists(TESTS_CSV):
        with open(TESTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('disease_id'):
                    cur.execute('''
                        INSERT OR REPLACE INTO disease_tests (
                            disease_id, disease_name, primary_specialty, recommended_tests
                        ) VALUES (?, ?, ?, ?)
                    ''', (
                        row.get('disease_id'), row.get('disease_name'), 
                        row.get('primary_specialty'), row.get('recommended_tests')
                    ))
    else:
        print(f"Warning: {TESTS_CSV} not found. Skipping disease tests ingestion.")

    conn.commit()
    conn.close()
    print("Database built successfully at", DB_PATH)

if __name__ == '__main__':
    build_db()
