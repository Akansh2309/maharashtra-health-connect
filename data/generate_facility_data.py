import csv
import random
from datetime import datetime, timedelta

def generate_dataset(filename="facility_availability.csv"):
    districts = ["Pune", "Nashik", "Nagpur", "Satara", "Gadchiroli", "Nandurbar", "Palghar", "Jalgaon", "Amravati"]
    facility_types = ["Sub-Centre", "PHC", "CHC", "District Hospital", "Rural Hospital"]
    specialties = ["General Medicine", "Obstetrics and Gynecology", "Pediatrics", "Cardiology", "Neurology", "Orthopedics", "Emergency Medicine", "Clinical Genetics", "Dermatology"]
    diagnostics = ["X-Ray", "Blood Test", "ECG", "Ultrasound", "MRI", "CT Scan", "None"]
    medicines = ["Paracetamol", "Amoxicillin", "Labetalol", "Oxytocin", "Iron/Folic Acid", "Metformin", "Insulin", "Aspirin", "Diazepam"]
    
    rows = []
    
    # Generate 150 records
    for i in range(1, 151):
        f_type = random.choice(facility_types)
        district = random.choice(districts)
        
        # Adjust capabilities based on facility type for realism
        if f_type == "District Hospital":
            emergency = "Yes"
            specialty = random.choice(specialties)
            tele = "Yes"
            diag = random.choice(["Ultrasound", "MRI", "X-Ray", "ECG", "Blood Test", "CT Scan"])
            ops = "24/7"
            doc_avail = random.choice(["Yes", "Yes", "No"]) # Higher chance
        elif f_type in ["CHC", "Rural Hospital"]:
            emergency = random.choice(["Yes", "Yes", "No"])
            specialty = random.choice(["General Medicine", "Obstetrics and Gynecology", "Pediatrics", "Emergency Medicine", "Orthopedics"])
            tele = random.choice(["Yes", "No"])
            diag = random.choice(["X-Ray", "Blood Test", "Ultrasound", "ECG", "None"])
            ops = "24/7"
            doc_avail = random.choice(["Yes", "No"])
        else: # PHC or Sub-Centre
            emergency = "No"
            specialty = "General Medicine"
            tele = random.choice(["Yes", "No", "No"]) # Lower chance of teleconsultation
            diag = random.choice(["Blood Test", "None"])
            ops = "08:00-18:00"
            doc_avail = random.choice(["Yes", "No"])
            
        pincode = random.randint(410000, 442999) # General range for Maharashtra
        facility_name = f"{district} {f_type} {random.randint(1, 100)}"
        
        if doc_avail == "Yes":
            # Next slot between now and next 3 days
            next_slot = (datetime.now() + timedelta(days=random.randint(0,3), hours=random.randint(1,10))).strftime("%Y-%m-%d %H:%M")
        else:
            next_slot = "N/A"
            
        med = random.choice(medicines)
        # Random stock level, some items might be out of stock
        stock = random.randint(50, 1000) if random.random() > 0.15 else 0
        
        row = {
            "facility_id": f"FAC{i:04d}",
            "facility_name": facility_name,
            "district": district,
            "village_or_pincode": str(pincode),
            "facility_type": f_type,
            "specialty": specialty,
            "doctor_available": doc_avail,
            "teleconsultation_available": tele,
            "next_slot": next_slot,
            "diagnostic_test_available": diag,
            "medicine_name": med,
            "medicine_in_stock": stock,
            "emergency_capable": emergency,
            "operating_hours": ops
        }
        rows.append(row)
        
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Generated {len(rows)} records in {filename}")

if __name__ == '__main__':
    generate_dataset()
