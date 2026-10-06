
# CryptoPulse AI

A polished full-stack cryptocurrency market dashboard prototype.

## Run in VS Code

1. Open this folder in VS Code.
2. Open Terminal.
3. Create a virtual environment:
   - Windows: `py -m venv .venv`
   - Activate: `.venv\Scripts\activate`
4. Install packages:
   `pip install -r requirements.txt`
5. Start:
   `python -m uvicorn main:app --reload`
6. Open:
   `http://127.0.0.1:8000`

The app uses CoinGecko market data when available and automatically shows fallback demo data if the API is temporarily unavailable.

## Project structure

- `main.py` — FastAPI backend and API routes
- `static/index.html` — responsive frontend, logo, dashboard and charts
- `requirements.txt` — Python dependencies
