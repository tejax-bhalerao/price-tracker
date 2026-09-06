# ⚡ PricePulse — E-Commerce Price Tracker

A clean, full-stack E-Commerce Price Tracking system built with **FastAPI**, **SQLAlchemy** (SQLite/PostgreSQL), **BeautifulSoup4**, and a responsive **Modern Web Dashboard UI**.

---

## 🌟 Highlights

- 🖥️ **Interactive Web UI Dashboard**: Modern dark-mode dashboard to track, search, filter, and monitor product prices visually.
- 📈 **Price History Trends & Charting**: Interactive Chart.js modal showing historical price trends against your target threshold.
- ⚡ **Instant On-Demand Price Check**: Check product prices with 1-click scraper execution and real-time toast feedback.
- 🔍 **Multi-Strategy Scraper**: Extracts prices automatically via JSON-LD, OpenGraph tags, and DOM selectors with fallback handling.
- 🗄️ **Zero-Config Database**: Works automatically with local SQLite (`pricetracker.db`) without requiring any external server installation.
- 📚 **FastAPI Swagger Docs**: Interactive API Explorer at `/docs`.

---

## 🏗️ Project Structure

```
price-tracker/
│
├── app/
│   ├── main.py                     # FastAPI app, static UI mounting & lifespan DB init
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── products.py         # Product CRUD, history, and on-demand check endpoints
│   │       └── users.py            # User registration & JWT authentication
│   │
│   ├── core/
│   │   ├── config.py               # Application settings (.env)
│   │   └── security.py             # Password hashing & JWT token handling
│   │
│   ├── database/
│   │   ├── base.py                 # SQLAlchemy Declarative Base
│   │   └── session.py              # Engine setup with automatic SQLite fallback
│   │
│   ├── models/
│   │   ├── user.py                 # User SQLAlchemy model
│   │   ├── product.py              # Product SQLAlchemy model
│   │   └── price_history.py        # PriceHistory SQLAlchemy model
│   │
│   ├── schemas/
│   │   ├── user.py                 # User Pydantic schemas
│   │   └── product.py              # Product & history Pydantic schemas
│   │
│   └── services/
│       ├── scraper.py              # Multi-strategy BeautifulSoup web scraper
│       ├── price_service.py        # Price check & alert orchestration
│       └── email_service.py        # SMTP / Mailtrap notification service
│
├── static/                         # Web Application Frontend
│   ├── index.html                  # Main Dashboard UI
│   ├── css/style.css               # Design System & Styling
│   └── js/app.js                   # Interactive UI Logic & Chart.js Integration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
└── README.md
```

---

## 🚀 How to Run the App (Step-by-Step)

### 1. Activate your Virtual Environment
In PowerShell / Command Prompt:
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies (if not already done)
```powershell
pip install -r requirements.txt
```

### 3. Start the Application
```powershell
uvicorn app.main:app --reload
```

### 4. Open in Browser
- 🖥️ **Web Dashboard UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 📖 **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📡 API Endpoints Reference

### Web UI
- `GET /`: Serves the interactive PricePulse web dashboard.

### Products (`/api/v1/products`)
- `POST /products/`: Add a new product to track (performs initial scrape)
- `GET /products/`: List all tracked products
- `GET /products/{id}`: Get product details with price history
- `PUT /products/{id}`: Update target price or active status
- `DELETE /products/{id}`: Stop tracking and delete product
- `POST /products/{id}/check-now`: Trigger on-demand price scrape and alert check
- `GET /products/{id}/history`: Fetch price timeline data for charts

### Authentication & Users (`/api/v1/users`)
- `POST /users/register`: Register new user account
- `POST /users/login`: Authenticate and receive JWT access token
- `GET /users/me`: View authenticated user profile
