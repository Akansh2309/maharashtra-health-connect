# 🏥 Maharashtra Health Connect

> **Smart Healthcare Accessibility for Every Citizen — Urban, Semi-Urban & Rural Maharashtra**

Built for **Smart India Hackathon 2026** | Problem Statement: **PS#26133** | Government of Maharashtra

**Developed by Team Kacchodis**

---

## 📋 Overview

Maharashtra Health Connect is a real-time healthcare accessibility dashboard that helps citizens find the nearest and best-equipped hospitals across Maharashtra. It features live bed availability, emergency triage routing, specialist filtering, budget estimation, and multilingual support (English, Hindi, Marathi).

## ✨ Key Features

| Feature | Description |
|---|---|
| 🗺️ **Interactive Map** | Leaflet-powered dark-themed map with hospital markers, clustering, and real-time routing |
| 🛏️ **Live Bed Availability** | Color-coded capacity indicators (Green/Yellow/Red) with hourly auto-refresh |
| 🚑 **Emergency Triage** | One-click emergency routing — Cardiac, Trauma, Breathing, Stroke, Pediatric, Burns |
| 🔍 **Smart Filters** | Filter by hospital type (Govt/Private/Rural), speciality, and budget |
| 🌐 **Multilingual (i18n)** | Full support for English, Hindi, and Marathi |
| ⭐ **Review System** | Users can rate and review hospitals with a 5-star system |
| 🔐 **Secure Auth** | Session-based authentication with rate limiting, CSRF protection, and security headers |
| 📱 **Responsive Design** | Glassmorphic dark UI that works across devices |

## 🛠️ Tech Stack

- **Frontend:** Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+)
- **Backend:** Python 3 (`http.server` + custom routing)
- **Map:** Leaflet.js + CARTO Dark Tiles
- **Icons:** Font Awesome 6
- **Auth:** SHA-256 hashed passwords, secure session cookies, rate limiting

## 📁 Project Structure

```
HACKATHON/
├── serve.py              # Main backend server (port 3000)
├── security.py           # Authentication, sessions, RBAC, rate limiting
├── auth_utils.py         # Legacy auth utilities
├── tests/
│   └── test_auth.py      # Authentication unit tests
├── public/               # Static frontend files
│   ├── index.html        # Dashboard (main page)
│   ├── login.html        # Login / Register page
│   ├── 404.html          # Custom 404 error page
│   ├── css/
│   │   ├── style.css     # Main dashboard styles
│   │   ├── login.css     # Login page styles
│   │   ├── base.css      # CSS variables & resets
│   │   ├── layout.css    # Grid & layout
│   │   ├── components.css # Reusable UI components
│   │   └── map.css       # Map-specific styles
│   ├── js/
│   │   ├── app.js        # Core application logic
│   │   ├── main.js       # API calls & data loading
│   │   ├── ui.js         # UI rendering & interactions
│   │   ├── map.js        # Map initialization & markers
│   │   ├── emergency.js  # Emergency triage system
│   │   ├── state.js      # Application state management
│   │   ├── login.js      # Login/Register form logic
│   │   ├── i18n.js       # Internationalization (EN/HI/MR)
│   │   └── hospitals-data.json  # Hospital dataset (65 hospitals)
│   └── img/
│       └── hospital_logo.png
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed on your system
- A modern web browser (Chrome, Firefox, Edge)

### Installation & Running

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/maharashtra-health-connect.git
cd maharashtra-health-connect

# 2. Start the server (no dependencies needed!)
python3 serve.py

# 3. Open in browser
# Navigate to http://localhost:3000
```

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `akansh@kacchodis.org` | `admin123` |
| User | `demo@kacchodis.org` | `demo` |

## 🔒 Security Features

- **SHA-256 Password Hashing** — No plaintext passwords stored
- **Session-based Auth** — Secure HTTP-only cookies with configurable TTL
- **Rate Limiting** — Brute-force protection on login/register endpoints
- **Security Headers** — CSP, X-Frame-Options, HSTS, X-Content-Type-Options, XSS Protection
- **Input Sanitization** — HTML escaping on all user inputs
- **RBAC** — Role-based access control (Admin/User)

## 📊 Dataset

The hospital dataset includes **65 hospitals** across Maharashtra covering:
- Government hospitals (district & sub-district)
- Private hospitals
- Rural health centers
- Emergency-equipped facilities

Each hospital entry includes: name, location, coordinates, bed count, specialties, type, budget range, rating, and emergency capabilities.

## 🌐 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/login` | ❌ | User login |
| `POST` | `/api/register` | ❌ | New user registration |
| `GET` | `/api/session` | ✅ | Get current session info |
| `GET` | `/api/hospitals` | ✅ | Fetch all hospitals |
| `GET` | `/api/hospitals/:id` | ✅ | Get hospital by ID |
| `GET` | `/api/reviews/:id` | ❌ | Get reviews for a hospital |
| `POST` | `/api/reviews` | ✅ | Submit a review |
| `GET` | `/api/logout` | ✅ | Destroy session & logout |

## 📸 Screenshots

_Add screenshots of your dashboard, login page, and emergency triage here._

## 👥 Team Kacchodis

Built with ❤️ for Smart India Hackathon 2026

---

**© 2026 Kacchodis. All rights reserved.**
