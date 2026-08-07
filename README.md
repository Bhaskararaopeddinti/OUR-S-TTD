# OURS TTD — AI Smart Pilgrim Companion

> **"Your Complete Digital Companion for a Safe, Peaceful & Smart Tirumala Pilgrimage."**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PWA Ready](https://img.shields.io/badge/PWA-Ready-orange)](https://web.dev/progressive-web-apps/)

---

## 📖 Project Overview

**OURS TTD** is a production-ready, hackathon-quality AI-powered multilingual web application built to assist pilgrims visiting the Sri Venkateswara Temple in Tirumala, Andhra Pradesh, India — managed by Tirumala Tirupati Devasthanams (TTD).

The platform provides:
- 🤖 **Gemini AI Assistant** — instant answers about temple rules, queue, facilities, food, dress code
- 🗺️ **Smart Navigation** — map with all key Tirumala locations
- 🚨 **Emergency SOS** — one-tap alert with geolocation to support desk
- 📋 **Booking Architecture** — ready for official TTD API integration
- 💚 **Health Monitoring** — reminders, health card, wheelchair requests
- 🔍 **Lost & Found** — report and search system
- 🛡️ **Admin Dashboard** — real-time analytics and emergency management
- 🌐 **8 Languages** — English, Telugu, Hindi, Tamil, Kannada, Malayalam, Marathi, Bengali
- 📱 **PWA** — installable, offline-capable web app

---

## ✨ Features

| Module | Status | Notes |
|---|---|---|
| Home Dashboard | ✅ Live | Queue, stats, quick services |
| AI Chat Assistant | ✅ Live | Gemini (fallback: keyword) |
| Queue Intelligence | ✅ Live | Official TTD public status |
| Smart Navigation | ✅ Live | OpenStreetMap / Google Maps |
| Emergency SOS | ✅ Live | Geolocation + DB alert |
| Darshan Booking | ✅ Architecture | Pending official TTD API |
| Health Monitoring | ✅ Live | Reminders + wheelchair request |
| Lost & Found | ✅ Live | Report + search |
| Admin Dashboard | ✅ Live | Analytics + alert table |
| Multi-language | ✅ Live | 8 languages via MyMemory API |
| PWA / Offline | ✅ Live | Service worker + manifest |
| Auth (JWT) | ✅ Live | Login + register + bcrypt |
| WebSocket | ✅ Live | Live push updates |
| Dark / Light Mode | ✅ Live | Persisted per user |

---

## 📁 Folder Structure

```
OURS-TTD/
├── frontend/
│   ├── index.html            # SPA entry point
│   ├── pages/                # SPA page fragments
│   │   ├── home.html
│   │   ├── dashboard.html
│   │   ├── booking.html
│   │   ├── navigation.html
│   │   ├── admin.html
│   │   ├── lostfound.html
│   │   └── health.html
│   ├── css/
│   │   ├── style.css         # Full design system
│   │   └── responsive.css    # Breakpoint overrides
│   ├── js/
│   │   ├── api.js            # API client (auth + public)
│   │   ├── app.js            # SPA router + all pages
│   │   ├── chatbot.js        # Gemini chatbot + TTS + STT
│   │   ├── queue.js          # WebSocket live updates
│   │   ├── sos.js            # Emergency SOS dialog
│   │   ├── navigation.js     # Maps integration
│   │   ├── voice.js          # Voice input
│   │   ├── language.js       # Translation
│   │   ├── notifications.js  # Notification bell
│   │   └── sw.js             # Service worker (PWA)
│   └── manifest.json         # PWA manifest
│
├── backend/
│   ├── main.py               # FastAPI app, seeding, WebSocket
│   ├── database.py           # SQLAlchemy engine + session
│   ├── models.py             # All ORM models
│   ├── schemas.py            # Pydantic schemas
│   ├── auth.py               # JWT + bcrypt
│   ├── requirements.txt
│   ├── routers/
│   │   ├── auth_routes.py    # /api/auth/*
│   │   └── core.py           # All pilgrim + admin APIs
│   └── services/
│       ├── ai_service.py     # Gemini integration
│       ├── ttd_official.py   # Public TTD status scraper
│       ├── google_translation.py # Translation (MyMemory)
│       ├── facilities_data.py
│       ├── queue_prediction.py
│       └── recommendation.py
│
├── .env                      # Secret keys (never commit)
├── .env.example              # Template
├── README.md
└── render.yaml               # Render.com deployment config
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip

### 1. Clone and enter the project
```bash
cd "OURS'S TDD"
```

### 2. Set up virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables
```bash
copy .env.example .env
# Edit .env and add your API keys
```

### 5. Start the server
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Open in browser
```
http://localhost:8000
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
# Database (SQLite for local dev; swap to PostgreSQL for production)
DATABASE_URL=sqlite:///./ours_ttd.db

# Security — generate a strong random key for production
SECRET_KEY=replace-with-a-long-random-secret

# CORS — set to your frontend domain in production
CORS_ORIGINS=*

# Gemini AI (optional — chatbot falls back to keyword mode without it)
GEMINI_API_KEY=your-gemini-api-key-here

# Google Maps (optional — OpenStreetMap used as fallback)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key-here
```

---

## 🤖 Gemini AI Setup

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Add it to `.env`:
   ```env
   GEMINI_API_KEY=your-key-here
   ```
4. Restart the server — the AI chatbot will use Gemini automatically

> **Without a key:** The chatbot uses comprehensive keyword-based responses covering all major TTD topics.

---

## 🗺️ Google Maps Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Maps JavaScript API** and **Maps Embed API**
3. Create an API key and restrict it to your domain
4. Add to `.env`:
   ```env
   GOOGLE_MAPS_API_KEY=your-key-here
   ```
5. In `frontend/js/navigation.js`, set the key in `GOOGLE_MAPS_API_KEY`

> **Without a key:** Navigation page uses OpenStreetMap (free, no key required).

---

## 🐘 PostgreSQL / Supabase Setup

The app uses SQLite by default for local development. To switch to PostgreSQL:

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Get the connection string from **Settings → Database**
3. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```
4. Delete the local `ours_ttd.db` and restart — tables will be auto-created

---

## 📡 API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, get JWT token |
| GET | `/api/queue` | Official TTD public status |
| GET | `/api/facilities` | Facility directory |
| POST | `/api/chat` | AI assistant (Gemini) |
| POST | `/api/sos` | Emergency SOS alert |
| GET | `/api/maps/locations` | Navigation GPS locations |
| POST | `/api/lostfound` | File lost/found report |
| GET | `/api/lostfound` | Search reports |
| POST | `/api/bookings` | Create booking request |
| GET | `/api/bookings` | List user bookings |
| POST | `/api/health/reminders` | Set health reminder |
| GET | `/api/notifications` | User notifications |
| GET | `/api/profile` | Get user profile |
| PUT | `/api/profile` | Update profile |
| GET | `/api/admin/analytics` | Admin stats (admin only) |
| GET | `/api/admin/emergencies` | All SOS alerts (admin only) |
| WS | `/ws/live` | WebSocket live updates |

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t ours-ttd .

# Run container
docker run -p 8000:8000 --env-file .env ours-ttd
```

Or with Docker Compose:
```bash
docker-compose up --build
```

---

## ☁️ Deploy to Render

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Set environment variables in the Render dashboard
5. Use the included `render.yaml` for automatic configuration

---

## 🔒 Security Notes

- **Never commit `.env`** — it's in `.gitignore`
- JWT tokens expire after 12 hours
- Passwords are hashed with bcrypt
- Rate limiting on all API endpoints (via `slowapi`)
- CORS configurable via `CORS_ORIGINS` env var
- SQL injection prevented by SQLAlchemy ORM
- XSS prevented by `textContent` (not `innerHTML`) for user data

---

## 🔭 Future Scope

- [ ] Official TTD booking API integration when available
- [ ] Google OAuth / social login
- [ ] Mobile OTP authentication
- [ ] Real-time crowd heatmap with WebGL
- [ ] Gemini Vision for dress code check (image upload)
- [ ] Push notifications (FCM)
- [ ] Offline language packs (pre-downloaded translations)
- [ ] PostgreSQL full-text search for Lost & Found
- [ ] Volunteer management system
- [ ] Analytics export (CSV/PDF)

---

## 📜 Data Policy

This application uses only **publicly available and verified information** about Tirumala/TTD:
- No fake queue times or booking slots are generated
- Features requiring official TTD APIs display: *"Available after official TTD integration"*
- The AI assistant is instructed to say "Please verify with TTD officials" when uncertain

---

## 👥 Credits

Built as a hackathon demonstration project for TTD pilgrimage assistance.

**Official TTD resources:**
- Website: [tirumala.org](https://tirumala.org)
- Booking: [ttdevasthanams.ap.gov.in](https://ttdevasthanams.ap.gov.in)
- Helpline: **155257**

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
