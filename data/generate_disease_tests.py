import csv
import random

def generate_tests():
    input_file = "disease_specialist_referral_mapping_hpo_2026-09-02.csv"
    output_file = "disease_diagnostic_tests.csv"
    
    test_mapping = {
        "Cardiology": ["ECG", "Echocardiogram", "Troponin Test", "Lipid Profile"],
        "Neurology": ["MRI Brain", "CT Scan Head", "EEG", "Nerve Conduction Study"],
        "Orthopedics": ["X-Ray", "MRI Joint", "Bone Density Scan", "CT Scan Bone"],
        "Dermatology": ["Skin Biopsy", "Blood Test (Allergy Panel)", "Dermoscopy"],
        "Clinical Genetics": ["Genetic Panel (WES/WGS)", "Karyotyping", "Chromosomal Microarray"],
        "Endocrinology": ["HbA1c", "Thyroid Profile (T3, T4, TSH)", "Fasting Blood Sugar", "Hormone Panel"],
        "Metabolic": ["Liver Function Test (LFT)", "Lipid Profile", "Blood Gas Analysis"],
        "Gastroenterology": ["Endoscopy", "Liver Function Test (LFT)", "USG Abdomen", "Stool Routine"],
        "Hepatology": ["Liver Function Test (LFT)", "USG Abdomen", "Viral Hepatitis Panel"],
        "Ophthalmology": ["Fundoscopy", "Visual Acuity Test", "Slit Lamp Exam", "OCT"],
        "Nephrology": ["Renal Function Test (RFT)", "Urine Routine", "USG KUB (Kidney/Bladder)"],
        "Pulmonology": ["Chest X-Ray", "Pulmonary Function Test (PFT)", "CT Thorax", "Sputum Culture"],
        "Respiratory": ["Chest X-Ray", "Arterial Blood Gas (ABG)", "Sputum Culture"],
        "Pediatrics": ["Complete Blood Count (CBC)", "Metabolic Screening", "Pediatric Ultrasound"],
        "Obstetrics": ["Obstetric Ultrasound", "Hemoglobin", "Urine Routine", "Glucose Tolerance Test"],
        "Gynecology": ["Pelvic Ultrasound", "Pap Smear", "Hormone Panel"],
        "Oncology": ["PET Scan", "Tumor Markers", "Biopsy", "CT Scan"],
        "Rheumatology": ["Rheumatoid Factor", "ANA Test", "ESR / CRP", "X-Ray Joint"],
        "Infectious Disease": ["Blood Culture", "CRP", "CBC", "Specific Viral/Bacterial Serology"],
        "Urology": ["Urine Culture", "Prostate Specific Antigen (PSA)", "USG Pelvis"],
        "ENT": ["Audiometry", "Nasal Endoscopy", "CT Paranasal Sinuses"],
        "Psychiatry": ["Psychiatric Evaluation", "Thyroid Profile (Rule out medical)", "Toxicology Screen"]
    }
    
    default_tests = ["Complete Blood Count (CBC)", "Basic Metabolic Panel (BMP)", "C-Reactive Protein (CRP)", "Urinalysis"]

    with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8', newline='') as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(["disease_id", "disease_name", "primary_specialty", "recommended_tests"])
        
        count = 0
        for row in reader:
            spec = row.get("primary_specialty", "").strip()
            possible_tests = None
            
            # Substring match for robust mapping
            for key, tests in test_mapping.items():
                if key.lower() in spec.lower():
                    possible_tests = tests
                    break
            
            if not possible_tests:
                possible_tests = default_tests
                
            # Pick 2 tests based on the specialty
            selected = random.sample(possible_tests, k=min(2, len(possible_tests)))
            
            # Common baseline tests are frequently ordered
            if "Complete Blood Count (CBC)" not in selected and random.random() > 0.6:
                selected.append("Complete Blood Count (CBC)")
                
            writer.writerow([row["disease_id"], row["disease_name"], spec, ", ".join(selected)])
            count += 1
            
    print(f"Generated mapped tests for {count} diseases in {output_file}")

if __name__ == '__main__':
    generate_tests()
