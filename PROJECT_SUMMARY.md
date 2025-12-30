# Real-Time Stock Market Data Pipeline

## 🎯 Overview
A production-grade, real-time data pipeline that streams stock market data from Finnhub API through Kafka, processes it with Spark, stores in PostgreSQL, and visualizes in a Streamlit dashboard.

## 📊 Architecture
Finnhub API → Producer → Kafka → Spark → PostgreSQL → Dashboard

## ✅ Status
- **Pipeline:** ✅ Fully operational
- **Containerization:** ✅ Complete (9 containers)
- **Data Flow:** ✅ Verified (245+ records)
- **Dashboard:** ✅ Live and auto-refreshing

## 🚀 Quick Start
```bash
docker-compose up -d
open http://localhost:8501
```

## 📈 Metrics
- **Stocks Tracked:** 5 (AAPL, GOOGL, MSFT, AMZN, TSLA)
- **Update Frequency:** 30 seconds
- **Processing Latency:** < 30 seconds
- **Data Retention:** Unlimited (PostgreSQL)
