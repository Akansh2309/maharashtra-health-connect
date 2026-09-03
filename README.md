# SehatSetu: Rural Public Healthcare Access & Continuity Platform

## 🏆 Smart India Hackathon 2026 
**Problem Statement:** #26133 - Accessibility and quality of public healthcare services in rural and underserved areas.
**Category:** Software (MedTech / HealthTech)

---

## 🚨 The Problem
Rural communities suffer from distance, specialist shortages, and fragmented health records. Meanwhile, ASHA workers and PHC staff are overwhelmed. High-risk patients (maternal, emergency, chronic) often get lost in the system when referred because there is no digital tracking, resulting in delayed care and poor outcomes.

## 🚀 Our Solution: SehatSetu
SehatSetu is a **digital care-coordination platform** built specifically for frontline health workers (ASHA/ANM) and public health facilities. It ensures no patient, referral, or follow-up is lost due to distance, language, or fragmented records.

### Key Features Developed (Hackathon MVP)
1. **Frontline Worker Registration & Triage:** 
   - A dedicated workflow for ASHA workers to register patients and input clinical vitals (BP, Temperature, Symptoms).
2. **Clinical Red-Flag Escalation:**
   - Automated rule-based engine that detects high-risk danger signs (e.g., high BP in pregnancy) and escalates for immediate referral.
3. **Smart Emergency Facility Routing:**
   - Instead of just finding the "nearest" hospital, the system filters for facilities with the exact required specialty (e.g., Pediatric/Maternal) and provides real-time, traffic-aware routing.
4. **Digital Referral & Teleconsultation:**
   - 1-click referral initiation that generates a simulated teleconsultation slot and confirms PHC medicine availability, closing the loop on patient care.
5. **Multilingual Offline-Ready Interface:**
   - Built-in support for English, Marathi, and Hindi, designed for low-literacy workflows.

---

## 💻 Tech Stack (Framework-Free & Secure)
- **Frontend:** Vanilla HTML, CSS, JavaScript (Zero bloat, blazing fast).
- **Backend:** Custom Python 3 HTTP Server (Modularized routing, state management, and strict security headers).
- **Mapping & Routing:** Leaflet.js with live Open Source Routing Machine (OSRM) integration.
- **Localization:** Custom i18n engine dynamically translating the DOM.

---

## 🏃‍♂️ How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Akansh2309/maharashtra-health-connect.git
   cd maharashtra-health-connect
   ```
2. **Start the secure local server:**
   ```bash
   python3 serve.py
   ```
3. **Open the App:**
   Navigate to `http://localhost:8000` in your browser.

---

## 🎥 The Winning Demo Scenario
When presenting to the judges, follow this flow:
1. Click the **[+] New Patient Triage** button in the bottom right (simulating an ASHA worker in a village).
2. Enter a patient's age and a high Blood Pressure reading (e.g., `150/90`). Select "High BP in Pregnancy" as the symptom.
3. Click **Analyze & Escalate**. The system will flag a **High Risk Pregnancy** and prompt an emergency referral.
4. Click **Find Emergency Facility**. The app isolates the map to equipped facilities.
5. Select a hospital and click **Initiate Referral & Teleconsultation** to demonstrate the closed-loop care continuity (Booking slot + Medicine confirmation + SMS alert).

*Built with passion for rural healthcare accessibility.*
