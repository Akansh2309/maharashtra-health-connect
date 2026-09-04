# Maharashtra Health Connect

A comprehensive, AI-powered health triage and referral system built for the Smart India Hackathon 2026. This platform is designed to assist frontline health workers (ASHA/ANM) in rural and underserved areas with offline-first clinical decision support.

## Features

*   **AI Disease Prediction:** Real-time ML inference using a K-Nearest Neighbors (KNN) model across 40 clinical symptoms to predict 5,500+ conditions.
*   **Vitals Triage Engine:** Rule-based triage system for 4 patient profiles (Maternal, Neonate, Child, Adult) to identify critical emergencies.
*   **Facility Routing:** Live geographic and specialty-based routing to 150 mapped healthcare facilities in Maharashtra.
*   **Digital Referrals & Follow-ups:** Automated creation of digital referrals and task management for ASHA workers.
*   **Teleconsultation:** Integrated WebRTC-ready teleconsultation workflow for remote doctor assistance.
*   **Medicine & Diagnostics lookup:** Search real-time medicine inventory and recommended diagnostic tests at nearby facilities.
*   **Multilingual Support:** English, Marathi, and Hindi interfaces.

## Project Structure

*   `serve.py`: Main Python HTTP server.
*   `api_routes.py`: API endpoint handlers.
*   `data_api.py`: Core logic for ML inference, SQLite database queries, and facility routing.
*   `Disease_symptom_predictor.joblib`: The trained ML model.
*   `data/hpo_database.db`: SQLite database containing facilities, diseases, and symptoms.
*   `public/`: Frontend HTML, CSS, and JS.
    *   `final.html`: The main unified application interface.

## Running the Application

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start the server:**
    ```bash
    python3 serve.py
    ```

3.  **Access the application:**
    Open your web browser and navigate to `http://localhost:3000/final.html`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
*Developed by The Kacchodis for SIH 2026*
