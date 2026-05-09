# 🧠 AI Business Decision Copilot

> An AI-powered ERP analytics platform that transforms raw business data into intelligent insights, anomaly alerts, forecasts, and AI-driven recommendations — your intelligent business advisor.

---

## 🎯 Project Overview

The **AI Business Decision Copilot** is a production-grade ERP analytics platform built for hackathons and real-world deployment. It connects to ERP data (Odoo, SAP, custom CSV exports), runs machine learning pipelines, and surfaces actionable intelligence through a beautiful dark-themed dashboard with an AI chatbot advisor.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Sales Analytics** | Revenue trends, product ranking, regional breakdown, category analysis |
| 🔮 **Forecasting** | Prophet-powered 7–90 day revenue & demand forecasts with confidence bands |
| ⚠️ **Anomaly Detection** | Isolation Forest + Z-score detection for revenue spikes, drops, and inventory risks |
| 💡 **Recommendations** | Restocking urgency, pricing optimization, customer retention actions |
| 🤖 **AI Assistant** | Claude-powered chatbot that answers business questions in natural language |
| 📦 **Inventory Health** | Days-of-stock tracking, stock-out risk classification, bubble chart visualisation |

---

## 🏗️ Architecture

```
ai_business_copilot/
├── app.py                          # Streamlit dashboard (main entry point)
├── backend/
│   ├── main.py                     # FastAPI REST API
│   ├── services/
│   │   ├── analytics_service.py    # KPIs, trends, segmentation
│   │   ├── forecasting_service.py  # Prophet time-series forecasting
│   │   ├── anomaly_service.py      # Isolation Forest anomaly detection
│   │   ├── recommendation_service.py # Rule + analytics recommendations
│   │   └── ai_chat_service.py      # Claude AI / built-in Q&A engine
│   └── utils/
│       └── data_loader.py          # CSV ingestion & validation
├── data/
│   ├── generate_sample_data.py     # Synthetic ERP data generator
│   └── erp_data.csv                # Generated 5,500-row sample dataset
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Data Flow

```
CSV Upload / ERP Export
        │
        ▼
  Data Loader (validation, type coercion)
        │
        ▼
┌───────────────────────────────────────────┐
│           Analytics Engine                │
│  Analytics │ Forecasting │ Anomaly │ Recs │
└───────────────────────────────────────────┘
        │
        ▼
  Streamlit Dashboard  ◄──► FastAPI REST API
        │
        ▼
    AI Chatbot (Claude / Built-in Engine)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Dashboard** | Streamlit 1.35, custom dark CSS |
| **API** | FastAPI 0.111, Pydantic v2, Uvicorn |
| **ML / Forecasting** | Prophet 1.1, Scikit-learn (Isolation Forest) |
| **Data** | Pandas, NumPy |
| **Visualisation** | Plotly 5.22 |
| **AI** | Anthropic Claude (claude-sonnet-4) |
| **Database** | PostgreSQL (optional), SQLAlchemy |
| **Deployment** | Docker, Docker Compose |

---

## ⚡ Quick Start

### 1. Clone & install

```bash
git clone https://github.com/yourname/ai-business-copilot.git
cd ai-business-copilot

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Generate sample data

```bash
python data/generate_sample_data.py
```

### 4. Launch the dashboard

```bash
streamlit run app.py
# Open http://localhost:8501
```

### 5. (Optional) Launch the API separately

```bash
uvicorn backend.main:app --reload --port 8000
# Docs at http://localhost:8000/docs
```

---

## 🐳 Docker Deployment

```bash
# Copy and edit env
cp .env.example .env

# Build and start all services
docker compose up --build

# Dashboard: http://localhost:8501
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

---

## 📡 API Endpoints

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service info |
| GET | `/health` | Health check + dataset stats |

### Data
| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload CSV file |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/kpi` | KPI summary |
| GET | `/analytics/monthly-revenue` | Monthly revenue & profit |
| GET | `/analytics/daily-revenue?days=90` | Daily revenue timeseries |
| GET | `/analytics/top-products?n=10` | Top products by revenue |
| GET | `/analytics/revenue-by-region` | Regional breakdown |
| GET | `/analytics/revenue-by-category` | Category breakdown |
| GET | `/analytics/customer-segments` | RFM customer segments |
| GET | `/analytics/inventory-status` | Inventory health |

### Forecasting
| Method | Endpoint | Description |
|---|---|---|
| GET | `/forecast/revenue?periods=30&product=Laptop` | Revenue forecast |
| GET | `/forecast/demand?periods=30` | Demand by product |
| GET | `/forecast/inventory-needs?safety_days=14` | Restock quantities |

### Anomaly Detection
| Method | Endpoint | Description |
|---|---|---|
| GET | `/anomalies/alerts` | Unified alert summary |
| GET | `/anomalies/revenue` | Revenue anomaly dates |
| GET | `/anomalies/products` | Product anomalies |
| GET | `/anomalies/inventory` | Inventory anomalies |

### Recommendations
| Method | Endpoint | Description |
|---|---|---|
| GET | `/recommendations/all` | All recommendations |
| GET | `/recommendations/restock` | Restock urgency list |
| GET | `/recommendations/pricing` | Pricing suggestions |
| GET | `/recommendations/retention` | Customer retention actions |

### AI Chat
| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | `{"question": "...", "history": [...]}` |

---

## 📊 Sample Dataset

The generated `erp_data.csv` contains **5,500+ rows** with these columns:

| Column | Type | Description |
|---|---|---|
| `date` | date | Transaction date (2024 full year) |
| `product_name` | str | 12 products across 3 categories |
| `category` | str | Electronics, Furniture, Stationery |
| `customer_id` | str | 200 unique customers (CUST_0001…) |
| `region` | str | North, South, East, West, Central |
| `quantity` | int | Units sold |
| `unit_price` | float | Sale price per unit |
| `revenue` | float | quantity × unit_price |
| `inventory` | int | Stock level at time of transaction |
| `cost` | float | COGS (60% of revenue) |
| `profit` | float | revenue − cost |
| `profit_margin` | float | % margin |

Seasonal patterns, anomalies, and realistic demand fluctuations are baked in.

---

## 🤖 AI Assistant Usage

The AI assistant works in two modes:

**Mode 1 — Claude AI (requires API key)**
Set `ANTHROPIC_API_KEY` in your `.env` file. The assistant uses the full Claude model with your ERP data as context.

**Mode 2 — Built-in Engine (no API key needed)**
Falls back to a keyword-matching analytics engine that generates structured, data-backed answers from the live dataset.

### Example questions
- `"Why did sales drop last month?"`
- `"Which product performs best?"`
- `"Predict next month revenue"`
- `"What are the top inventory risks?"`
- `"How can I improve customer retention?"`
- `"Summarize overall business performance"`

---

## 🔮 ML Models

### Forecasting — Prophet
- Weekly + yearly seasonality detection
- Automatic changepoint detection
- Confidence interval bands
- Falls back to 30-day moving average when data is sparse

### Anomaly Detection — Isolation Forest
- Contamination rate: 5% (configurable)
- Features: daily revenue, order count, 7-day moving average, day-over-day % change
- Z-score complementary method for product-level and inventory anomalies

### Customer Segmentation — RFM
- Recency, Frequency, Monetary scoring (1–3 each)
- Segments: At-Risk (3–4), Loyal (5–6), Champions (7–9)

---

## 📈 Screenshots

*(Run the app and capture screenshots for your presentation)*

| Screen | Description |
|---|---|
| Dashboard Home | KPI cards + monthly revenue chart |
| Forecasting Tab | Prophet forecast with confidence bands |
| Anomaly Tab | Revenue timeline with spike/drop markers |
| AI Chat | Conversation with business advisor |
| Inventory Tab | Health dashboard + bubble chart |

---

## 🚀 Future Scope

- [ ] Live Odoo / SAP ERP connector via REST API
- [ ] PostgreSQL persistent data store with historical tracking
- [ ] Email/Slack alert notifications for high-severity anomalies
- [ ] Multi-tenant support for multiple businesses
- [ ] TensorFlow LSTM model for improved long-range forecasting
- [ ] Scheduled batch jobs (Celery + Redis)
- [ ] Role-based access control (admin / analyst / viewer)
- [ ] Mobile-responsive React frontend
- [ ] Exportable PDF / Excel reports

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*Built for hackathon excellence. Production-ready architecture. AI-powered business intelligence.*
