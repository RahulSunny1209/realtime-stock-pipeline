# 📈 Real-Time Stock Market Data Pipeline

A production-grade, real-time data engineering pipeline that ingests, processes, and visualizes live stock market data.

![Pipeline Architecture](docs/architecture-diagram.png)

## 🎯 Project Overview

This project demonstrates a complete real-time data pipeline using modern data engineering tools and best practices. It fetches live stock data from Polygon.io, streams it through Apache Kafka, processes it with Apache Spark, stores it in PostgreSQL, and visualizes it on a Streamlit dashboard.

## 🏗️ Architecture
```
┌─────────────────┐
│  Polygon.io API │  ← Live stock data (AAPL, GOOGL, MSFT, AMZN, TSLA)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Kafka Producer  │  ← Fetch every 60s with smart caching
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apache Kafka    │  ← Message queue (stock-prices topic)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Spark Processor │  ← Calculate moving averages & indicators
└────────┬────────┘
         │
         ├──────────────┐
         ▼              ▼
┌──────────────┐  ┌──────────┐
│ PostgreSQL   │  │  Redis   │  ← Time-series data & cache
└──────────────┘  └──────────┘
         │
         ▼
┌─────────────────┐
│    Streamlit    │  ← Real-time dashboard
└─────────────────┘
```

## 🛠️ Tech Stack

- **Language**: Python 3.11.14
- **Message Queue**: Apache Kafka 3.5
- **Stream Processing**: Apache Spark (PySpark 3.5.0)
- **Database**: PostgreSQL
- **Caching**: Redis
- **Visualization**: Streamlit
- **Containerization**: Docker & Docker Compose
- **Data Source**: Polygon.io API
- **Development**: VS Code, Git

## ✨ Features

### ✅ Implemented (Phase 1-2)
- [x] Real-time stock data ingestion from Polygon.io
- [x] Apache Kafka streaming pipeline
- [x] Smart metadata caching (6-hour TTL)
- [x] Rate limit protection
- [x] Retry logic with exponential backoff
- [x] Comprehensive logging and metrics
- [x] Kafka UI for monitoring
- [x] Consumer for data verification
- [x] Docker containerization for Kafka stack

### 🔄 In Progress (Phase 3)
- [ ] Apache Spark stream processing
- [ ] Moving averages calculation
- [ ] Technical indicators (RSI, MACD)

### 📅 Planned (Phase 4-8)
- [ ] PostgreSQL time-series storage
- [ ] Redis caching layer
- [ ] Streamlit real-time dashboard
- [ ] AWS cloud deployment
- [ ] CI/CD pipeline
- [ ] Monitoring & alerting

## 🚀 Quick Start

### Prerequisites
- MacBook M2 (or compatible Apple Silicon)
- Python 3.11+
- Docker Desktop
- Polygon.io API key (free tier)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd realtime-stock-pipeline
```

2. **Create virtual environment**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your POLYGON_API_KEY
```

5. **Start Kafka cluster**
```bash
docker-compose up -d
```

6. **Run the producer**
```bash
python src/producer/stock_producer.py
```

7. **In another terminal, run the consumer**
```bash
python src/consumer/stock_consumer.py
```

8. **Access Kafka UI**
```
http://localhost:8080
```

## 📂 Project Structure
```
realtime-stock-pipeline/
├── README.md
├── docker-compose.yml          # Kafka stack configuration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not committed)
├── .gitignore
├── docs/
│   ├── architecture.md         # Detailed architecture docs
│   ├── setup.md               # Setup instructions
│   └── medium-posts/          # Blog posts
├── src/
│   ├── producer/
│   │   └── stock_producer.py  # Kafka producer
│   ├── consumer/
│   │   └── stock_consumer.py  # Kafka consumer
│   ├── processing/
│   │   └── spark_processor.py # Spark stream processing
│   ├── storage/
│   │   └── database.py        # PostgreSQL operations
│   ├── dashboard/
│   │   └── app.py             # Streamlit dashboard
│   └── utils/
│       ├── config.py          # Configuration utilities
│       └── logger.py          # Logging setup
├── config/
│   ├── kafka_config.py        # Kafka configuration
│   ├── spark_config.py        # Spark configuration
│   └── db_config.py           # Database configuration
├── tests/
│   └── test_pipeline.py       # Unit tests
└── scripts/
    ├── setup_kafka.sh         # Kafka setup script
    ├── setup_postgres.sh      # PostgreSQL setup script
    └── deploy.sh              # Deployment script
```

## 📊 Current Status

**Phase 2 Complete**: Kafka Producer & Consumer
- ✅ Real-time data flowing through Kafka
- ✅ 5 stocks monitored (AAPL, GOOGL, MSFT, AMZN, TSLA)
- ✅ Production-grade error handling
- ✅ Metrics tracking and monitoring

**Next**: Phase 3 - Spark Stream Processing

## 🎓 Key Design Decisions

### Why Polygon.io over Yahoo Finance?
- **Reliability**: Official market data API vs web scraping
- **Rate Limits**: Predictable limits (5 calls/min free tier)
- **Documentation**: Clear API docs and entitlements
- **Production-Ready**: Suitable for real-time systems

### Caching Strategy
- **Metadata TTL**: 6 hours (company info changes rarely)
- **Price Data**: No caching (needs to be real-time)
- **Benefits**: Reduced API calls, respects rate limits

### Retry Logic
- **Exponential Backoff**: 1s, 2s, 4s
- **Max Retries**: 3 attempts
- **Graceful Degradation**: Continues with other symbols

## 📝 Blog Posts

1. [Phase 1: Environment Setup](https://medium.com/@kothagundlarahul/how-i-built-a-real-time-stock-market-data-pipeline-f817e5098e7d)
2. [Phase 2: Kafka Producer] (Coming soon)

## 👨‍💻 Author

**Rahul Kothagundla**
- MacBook M2
- Learning Data Engineering
- [LinkedIn](your-linkedin) | [Medium](https://medium.com/@kothagundlarahul) | [GitHub](your-github)

## 📄 License

MIT License

## 🙏 Acknowledgments

- Inspired by real-world data engineering practices
- Built for learning and portfolio development
- Special thanks to the data engineering community

---

**⭐ If you found this helpful, please star the repository!**

Built with ❤️ on MacBook M2
