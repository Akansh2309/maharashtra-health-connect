<p align="center">
  <img src="https://img.shields.io/badge/SIH_2026-PS%2326133-orange?style=for-the-badge" alt="SIH 2026" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Leaflet.js-Map_Engine-green?style=for-the-badge&logo=leaflet&logoColor=white" alt="Leaflet" />
  <img src="https://img.shields.io/badge/License-All_Rights_Reserved-red?style=for-the-badge" alt="License" />
</p>

<h1 align="center">Maharashtra Health Connect</h1>

<p align="center">
  <b>Smart Healthcare Accessibility for Every Citizen</b><br/>
  Urban · Semi-Urban · Rural Maharashtra
</p>

<p align="center">
  Built for <b>Smart India Hackathon 2026</b> | Problem Statement <b>#26133</b> | Government of Maharashtra<br/>
  <sub>Developed by <b>Team Kacchodis</b></sub>
</p>

---

## About The Project

Maharashtra Health Connect is a **real-time healthcare accessibility dashboard** designed to bridge the gap between citizens and critical medical infrastructure across the state of Maharashtra.

The platform empowers users — from urban professionals to rural residents — to instantly locate the nearest hospitals, assess live bed availability, filter by medical specialty and budget, and receive emergency triage routing to the best-equipped facility within seconds.

### The Problem

> Citizens in Maharashtra — especially in semi-urban and rural areas — face significant challenges in identifying nearby hospitals, understanding bed availability, and accessing emergency care in time. There is no unified, real-time system that aggregates hospital data across government and private facilities statewide.

### Our Solution

A unified, dark-themed, map-driven dashboard that aggregates **65+ hospitals** across **30+ districts**, providing:

- **Live bed availability** with color-coded capacity indicators
- **Emergency triage routing** for six critical emergency categories
- **Specialist and budget filtering** to match patients with the right facility
- **Multilingual support** in English, Hindi, and Marathi
- **Secure authentication** with role-based access control

---

## Key Features

| Feature | Description |
|:--------|:------------|
| **Interactive Map** | Leaflet-powered dark-themed map with hospital markers, real-time routing, and distance calculation |
| **Live Bed Tracking** | Color-coded capacity indicators — `Green` (available), `Yellow` (filling), `Red` (critical) — with hourly auto-refresh |
| **Emergency Triage** | One-click emergency routing across six categories: Cardiac, Trauma, Breathing, Stroke, Pediatric, Severe Burns |
| **Smart Filters** | Filter hospitals by type (Govt / Private / Rural / ER), medical specialty, and estimated budget |
| **Multilingual (i18n)** | Full interface translation in English, Hindi, and Marathi with one-click language switching |
| **Review System** | Authenticated users can rate hospitals on a 5-star scale and leave written reviews |
| **Secure Auth** | SHA-256 password hashing, session cookies, rate limiting, CSRF protection, and strict HTTP security headers |
| **Responsive UI** | Glassmorphic dark interface with smooth animations, optimized for desktop and tablet viewports |

---

## Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND                                               │
│  ├── HTML5 (Semantic)                                   │
│  ├── CSS3 (Glassmorphism, Custom Properties, Flexbox)   │
│  ├── JavaScript ES6+ (Vanilla, No Frameworks)           │
│  ├── Leaflet.js (Map Engine)                            │
│  ├── CARTO Dark Tiles (Map Theme)                       │
│  └── Font Awesome 6 (Icon Library)                      │
├─────────────────────────────────────────────────────────┤
│  BACKEND                                                │
│  ├── Python 3 (http.server + Custom Router)             │
│  ├── SHA-256 Password Hashing                           │
│  ├── Session-based Authentication (Secure Cookies)      │
│  ├── Rate Limiting (In-memory)                          │
│  └── Content Security Policy (CSP) + HSTS               │
└─────────────────────────────────────────────────────────┘
```

**Zero external dependencies.** The entire backend runs on Python's standard library. No `pip install` required.

---

## Project Structure

```
maharashtra-health-connect/
│
├── serve.py                  # Main HTTP server (port 3000)
├── security.py               # Auth, sessions, RBAC, rate limiting
├── auth_utils.py             # Legacy authentication utilities
│
├── tests/
│   └── test_auth.py          # Unit tests for authentication
│
├── public/                   # Static frontend (served by Python)
│   ├── index.html            # Dashboard — main application page
│   ├── login.html            # Login & registration page
│   ├── 404.html              # Custom error page
│   │
│   ├── css/
│   │   ├── base.css          # CSS custom properties & resets
│   │   ├── layout.css        # Grid system & page structure
│   │   ├── components.css    # Reusable UI component styles
│   │   ├── style.css         # Dashboard-specific styles
│   │   ├── login.css         # Login page styles
│   │   └── map.css           # Map container & marker styles
│   │
│   ├── js/
│   │   ├── app.js            # Core application logic & initialization
│   │   ├── main.js           # API calls, data loading, review submission
│   │   ├── ui.js             # UI rendering, hospital cards, detail panel
│   │   ├── map.js            # Leaflet map initialization & markers
│   │   ├── emergency.js      # Emergency triage system
│   │   ├── state.js          # Centralized application state
│   │   ├── login.js          # Login & register form logic
│   │   ├── i18n.js           # Internationalization (EN / HI / MR)
│   │   └── hospitals-data.json   # Dataset: 65 hospitals across MH
│   │
│   ├── img/
│   │   └── hospital_logo.png
│   └── assets/
│       └── logo.png
│
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.10 or higher** — Check with `python3 --version`
- A modern web browser (Chrome, Firefox, or Edge)
- No additional packages or dependencies required

### Installation

```bash
# Clone the repository
git clone https://github.com/Akansh2309/maharashtra-health-connect.git

# Navigate into the project directory
cd maharashtra-health-connect

# Start the server
python3 serve.py
```

The server will start on **http://localhost:3000**. Open this URL in your browser.

### Demo Credentials

| Role  | Email                    | Password   |
|:------|:-------------------------|:-----------|
| Admin | `akansh@kacchodis.org`   | `admin123` |
| User  | `demo@kacchodis.org`     | `demo`     |

---

## Security Architecture

The backend implements **defense-in-depth** security across multiple layers:

```
Request Flow:

  Client ──► Rate Limiter ──► Session Validator ──► RBAC ──► Handler
                  │                   │                │
                  ▼                   ▼                ▼
            429 Too Many        401 Unauth        403 Forbidden
```

| Layer | Implementation |
|:------|:---------------|
| **Password Storage** | SHA-256 hashing — no plaintext passwords stored anywhere |
| **Session Management** | Cryptographic session IDs via `uuid4`, stored in HTTP-only cookies |
| **Rate Limiting** | Per-IP request throttling on login and registration endpoints |
| **Security Headers** | `Content-Security-Policy`, `X-Frame-Options: DENY`, `HSTS`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection` |
| **Input Sanitization** | All user-submitted text is HTML-escaped and length-capped before storage |
| **Access Control** | Role-based permissions — Admin and User roles with distinct capabilities |
| **Session Expiry** | Automatic cleanup of expired sessions via background thread |

---

## API Reference

All API endpoints return JSON. Authentication is session-based via cookies.

### Authentication

| Method | Endpoint          | Auth Required | Description              |
|:-------|:------------------|:--------------|:-------------------------|
| `POST` | `/api/login`      | No            | Authenticate a user      |
| `POST` | `/api/register`   | No            | Register a new account   |
| `GET`  | `/api/session`    | No            | Check current session    |
| `GET`  | `/api/logout`     | Yes           | Destroy session, redirect to login |

### Hospital Data

| Method | Endpoint              | Auth Required | Description                    |
|:-------|:----------------------|:--------------|:-------------------------------|
| `GET`  | `/api/hospitals`      | Yes           | Fetch all 65 hospitals         |
| `GET`  | `/api/hospitals/:id`  | Yes           | Fetch a single hospital by ID  |

### Reviews

| Method | Endpoint            | Auth Required | Description                    |
|:-------|:--------------------|:--------------|:-------------------------------|
| `GET`  | `/api/reviews/:id`  | No            | Get reviews for a hospital     |
| `POST` | `/api/reviews`      | Yes           | Submit a new review            |

---

## Dataset

The hospital dataset covers **65 facilities** across Maharashtra, including:

| Category | Count | Examples |
|:---------|:------|:---------|
| Government Hospitals | 30+ | KEM, JJ Hospital, Sassoon, GMC Nagpur |
| Private Hospitals | 20+ | Lilavati, Hinduja, Ruby Hall, Jupiter |
| Rural Health Centers | 15+ | PHCs and CHCs across Ratnagiri, Gadchiroli, Yavatmal |
| Emergency-Equipped | 40+ | Facilities with 24/7 ER, trauma, and ICU capabilities |

Each entry includes: name, GPS coordinates, district, bed count, specialties, type classification, budget tier, user rating, and emergency capabilities.

---

## Screenshots

> _Screenshots of the dashboard, login page, emergency triage panel, and hospital detail view can be added here._

<!--
To add screenshots, place them in the `public/img/` folder and reference them like:
![Dashboard](public/img/screenshot_dashboard.png)
![Login](public/img/screenshot_login.png)
-->

---

## Roadmap

- [x] Core dashboard with hospital listing and map
- [x] Emergency triage routing system
- [x] Multilingual interface (EN / HI / MR)
- [x] Secure authentication with rate limiting
- [x] Hospital review and rating system
- [ ] Real-time bed data integration via NHM/NIC APIs
- [ ] Ambulance tracking and ETA estimation
- [ ] SMS/WhatsApp alerts for bed availability
- [ ] PWA support for offline access in rural areas
- [ ] Integration with Ayushman Bharat Digital Mission (ABDM)

---

## Contributing

This project was built as part of SIH 2026. If you would like to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## Acknowledgements

- **Government of Maharashtra** — Problem statement and domain guidance
- **National Health Mission (NHM)** — Hospital data references
- **OpenStreetMap & CARTO** — Map tile services
- **Leaflet.js** — Open-source map library
- **Font Awesome** — Icon library

---

<p align="center">
  <b>Maharashtra Health Connect</b><br/>
  Smart India Hackathon 2026 · Problem Statement #26133<br/>
  <sub>Copyright 2026 Team Kacchodis. All rights reserved.</sub>
</p>
