<div align="center">
  <img src="https://img.shields.io/badge/Status-Live_on_Render-brightgreen?style=for-the-badge" alt="Status Badge"/>
  <img src="https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge"/>
  <img src="https://img.shields.io/badge/Machine_Learning-KNN-orange?style=for-the-badge" alt="ML Badge"/>
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License Badge"/>

  <h1>Maharashtra Health Connect</h1>
  <p><b>Advanced Clinical Decision Support & Tele-triage System</b></p>
  
  <br/>
  
  <a href="https://maharashtra-health-connect.onrender.com/final.html">
    <img src="https://img.shields.io/badge/View_Live_Demo-000000?style=for-the-badge&logo=render&logoColor=white" alt="Live Demo"/>
  </a>
</div>

<br/>

> A comprehensive, AI-powered health triage and referral system built for the Smart India Hackathon 2026. This platform is designed to assist frontline health workers (ASHA/ANM) in rural and underserved areas with offline-first clinical decision support.

<hr/>

## Core Features

*   **AI Disease Prediction:** Real-time Machine Learning inference utilizing a K-Nearest Neighbors (KNN) model. Evaluates across 40 clinical symptoms to accurately predict over 5,500 conditions.
*   **Vitals Triage Engine:** A strict, rule-based triage system customized for 4 distinct patient profiles (Maternal, Neonate, Child, Adult) to identify critical emergencies instantly.
*   **Dynamic Facility Routing:** Live geographic and specialty-based routing to 150 mapped healthcare facilities across Maharashtra, ensuring patients are sent to capable centers.
*   **Digital Referrals & Follow-ups:** Automated creation of digital referrals and task management for ASHA workers, ensuring zero loss to follow-up.
*   **Teleconsultation Bridge:** Integrated WebRTC-ready teleconsultation workflow for remote doctor assistance during critical emergencies.
*   **Medicine & Diagnostics Inventory:** Real-time lookup for medicine inventory and recommended diagnostic tests at nearby facilities.
*   **Multilingual Support:** Seamless UI toggling between English, Marathi, and Hindi to support grassroots workers.

## Project Architecture

The application is built on a lightweight, high-performance Python backend serving a highly interactive frontend.

```text
├── Disease_symptom_predictor.joblib  # Trained ML model (3.8MB)
├── data/
│   └── hpo_database.db               # SQLite DB (Facilities, Diseases, Symptoms)
├── render.yaml                       # Automated Render deployment blueprint
├── serve.py                          # Primary Python HTTP server
├── api_routes.py                     # API endpoint handlers
├── data_api.py                       # ML inference & facility routing logic
└── public/
    └── final.html                    # Unified application interface
```

## Running the Application Locally

**1. Install required dependencies**
```bash
pip install -r requirements.txt
```

**2. Launch the backend server**
```bash
python3 serve.py
```

**3. Access the application**
Open your preferred web browser and navigate to `http://localhost:3000/final.html`

<hr/>

<div align="center">
  <p>Developed with precision by <b>The Kacchodis</b> for SIH 2026</p>
</div>
