# RoMountainAgent - Intelligent Mountain Guide for the Romanian Carpathians

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20Lite-4285F4.svg)](https://ai.google.dev/)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900.svg)](https://leafletjs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**RoMountainAgent** is an intelligent, multi-agent AI assistant specializing exclusively in Romanian Carpathian hiking routes (Fagaras, Bucegi, Piatra Craiului, Retezat, Ceahlau, Parang, Apuseni, Ciucas, etc.).

It is accessible as a **mobile-first Progressive Web App (PWA)** for phones and desktops, featuring an **Agent-to-Agent (A2A) Mountain Cartographer**, interactive Leaflet topographic maps, live high-altitude weather, Salvamont safety advisories, 1-tap offline Markdown trail dossier downloads, and passcode access protection.

---

## Architecture & Multi-Agent Design

The system implements an Agent-to-Agent (A2A) orchestration pattern:
1. **RoMountainGuide (Lead Alpine Guide Agent)**:
   - Processes hiker inquiries in their native language (Romanian, English, Spanish, etc.).
   - Uses function calling to query real-time Open-Meteo alpine weather, OpenStreetMap hiking trail relations, and official Salvamont rules.
   - Generates standardized 6-section Mountain Trail Dossiers.
2. **Mountain Cartographer Agent (GIS Specialist)**:
   - Evaluates the route recommendations from the Lead Guide.
   - Extracts and verifies GPS waypoints (trailheads, cabins, springs, passes, summits) against an internal ground-truth Carpathian GIS database.
   - Emits structured map specifications rendered dynamically in the web UI as touch-friendly, pan-and-zoom Leaflet topographic maps.

---

## Key Features

- **Standardized Trail Dossier**: Structured format covering Mountain Massif, Starting Point, Official Markings (Stripe/Triangle/Cross/Dot), Difficulty, Duration, and Elevation Gain (+/-).
- **Interactive Topographic Maps**: Dynamically plotted Leaflet route maps with color-coded waypoints (trailheads, alpine huts, water springs, saddles, peaks).
- **Live Mountain Weather & Alerts**: Open-Meteo forecast API integration with automatic coordinate resolution for 20+ Romanian peaks (Omu, Moldoveanu, Toaca, Babele, etc.), apparent temperature, ridge wind gust warnings, and freezing alerts.
- **Salvamont Safety & Hazards**: High-wind alerts (>40-60 km/h), lightning hazard warnings, bear safety protocols, and emergency numbers (0-SALVAMONT / 112).
- **Offline 1-Tap Dossier Export**: Saves full structured trail dossiers directly to your mobile device (`.md`) for offline reading without cellular reception in remote valleys.
- **Client-Friendly Token Tracking**: Live token usage pill next to message timestamps showing prompt and completion token counts.
- **Interactive Stop Button**: Allows hikers to immediately cancel response generation in real time.
- **Passcode Access Gate**: Enforces a configurable passcode (`APP_ACCESS_PASSCODE`) so only authorized hikers consume your API quota.

---

## Quick Start (Local Run)

### 1. Clone the Repository
```bash
git clone https://github.com/elena-silvia/HikeAI.git
cd HikeAI
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to add your Google Gemini API key:
```env
MODEL=gemini-3.5-flash-lite
GOOGLE_API_KEY=your_gemini_api_key_here
KNOWLEDGE_SOURCE=local
LOCAL_KNOWLEDGE_DIRECTORY=knowledge
APP_ACCESS_PASSCODE=carpathians2026
```

### 3. Install Dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the Web App
```bash
python app_server.py
```
Open `http://localhost:8000` in your browser. Enter passcode `carpathians2026`.

---

## Deploy Free 24/7 on Render

To let friends access the guide from their phones without keeping your computer on:

1. Create a free account at [render.com](https://render.com).
2. Click **New +** > **Web Service** and connect your GitHub repository (`HikeAI`).
3. Set the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app_server:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   - `GOOGLE_API_KEY`: *(Your Google AI Studio Gemini API Key)*
   - `APP_ACCESS_PASSCODE`: *(Set your own private secret passcode for you and your friends)*
   - `MODEL`: `gemini-3.5-flash-lite`
5. Click **Deploy**. Render will generate a public HTTPS URL (e.g., `https://romountainagent.onrender.com`).

---

## Testing

The project includes an automated test suite verifying FastAPI endpoints, security authentication, diacritics file exports, Overpass API, Open-Meteo weather API, Cartographer A2A integration, and JSON storage:

```bash
pytest -v
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
