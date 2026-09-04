<div align="center">
  <img src="https://img.shields.io/badge/Status-Live_on_Render-brightgreen?style=for-the-badge" alt="Status Badge"/>
  <img src="https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge"/>
  <img src="https://img.shields.io/badge/Machine_Learning-KNN-orange?style=for-the-badge" alt="ML Badge"/>
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License Badge"/>

  <br/>
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=900&size=40&pause=1000&color=10B981&center=true&vCenter=true&width=800&height=80&lines=MAHARASHTRA+HEALTH+CONNECT" alt="Maharashtra Health Connect" />
  <p><b>Advanced Clinical Decision Support & Tele-triage System</b></p>
  
  <br/>
  
  <a href="https://maharashtra-health-connect.onrender.com/final.html">
    <img src="https://img.shields.io/badge/View_Live_Demo-000000?style=for-the-badge&logo=render&logoColor=white" alt="Live Demo"/>
  </a>
</div>

<br/>

> A comprehensive, AI-powered health triage and referral system built for the Smart India Hackathon 2026. This platform is designed to assist frontline health workers (ASHA/ANM) in rural and underserved areas with offline-first clinical decision support.

<hr/>

## CORE FEATURES

| Subsystem | Technical Description |
| :--- | :--- |
| **AI Disease Prediction** | Real-time Machine Learning inference utilizing a `K-Nearest Neighbors` (KNN) model. Evaluates across 40 clinical symptoms to accurately predict over 5,500 conditions. |
| **Vitals Triage Engine** | A strict, rule-based triage architecture customized for 4 distinct patient profiles (Maternal, Neonate, Child, Adult) to identify critical emergencies instantly. |
| **Dynamic Facility Routing** | Live geographic and specialty-based routing to 150 mapped healthcare facilities across Maharashtra, ensuring patients are sent to capable centers. |
| **Digital Referrals** | Automated creation of digital referrals and task management for ASHA workers, ensuring zero loss to follow-up. |
| **Teleconsultation Bridge** | Integrated WebRTC-ready teleconsultation workflow for remote doctor assistance during critical emergencies. |
| **Diagnostics Inventory** | Real-time lookup for medicine inventory and recommended diagnostic tests at nearby facilities. |
| **Multilingual Support** | Seamless UI toggling between English, Marathi, and Hindi to support grassroots workers. |

<br/>

## PROJECT ARCHITECTURE

The application is built on a lightweight, high-performance Python backend serving a highly interactive frontend.

```bash
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

<br/>

## DEPLOYMENT & USAGE

### 1. Live Cloud Deployment
The system is actively deployed and hosted on Render. You can access the production environment directly via the live demo link above, or by navigating to:
<kbd>https://maharashtra-health-connect.onrender.com/final.html</kbd>

### 2. Local Environment Setup

Install required dependencies:
```bash
pip install -r requirements.txt
```

Launch the backend server:
```bash
python3 serve.py
```


<hr/>

<div align="center">
  <p>Developed with precision by <b>The Kacchodis</b> for SIH 2026</p>
</div>

<div align="right">
  <br/><br/>
  <i>- Akansh Shaw</i>
</div>
