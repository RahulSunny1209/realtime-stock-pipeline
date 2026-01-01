# 📈 Real-Time Stock Market Data Pipeline

> A production-grade, end-to-end data engineering project demonstrating real-time data streaming, processing, and visualization.


## 🎯 Project Overview

A **real-time data pipeline** that streams live stock market data from Finnhub API, processes it through Apache Kafka and Spark, stores it in PostgreSQL, and visualizes it in an interactive Streamlit dashboard.

**Live Demo:** [Coming Soon - AWS Deployment]

---

## 🏗️ Architecture
```
┌─────────────┐    ┌─────────┐    ┌─────────┐    ┌──────────────┐    ┌───────────┐
│  Finnhub    │───▶│  Kafka  │───▶│  Spark  │───▶│ PostgreSQL   │───▶│ Dashboard │
│     API     │    │ (3 part)│    │Streaming│    │(Time-series) │    │(Streamlit)│
└─────────────┘    └─────────┘    └─────────┘    └──────────────┘    └───────────┘
                                        │
                                        ▼
                                   ┌─────────┐
                                   │  Redis  │
                                   │ (Cache) │
                                   └─────────┘
```

---

## ✨ Key Features

### 🚀 **Real-Time Data Streaming**
- Fetches live stock data every 30 seconds from Finnhub API
- Tracks 5 major stocks: AAPL, GOOGL, MSFT, AMZN, TSLA
- Handles 10+ data points per stock (price, volume, high, low, etc.)

### ⚡ **Stream Processing**
- Apache Spark Structured Streaming for real-time processing
- 30-second micro-batches with exactly-once semantics
- Windowed aggregations (5-min, 15-min, 30-min moving averages)
- Automatic checkpointing for fault tolerance

### 💾 **Persistent Storage**
- PostgreSQL for time-series data storage
- Redis for hot data caching (5-minute TTL)
- Indexed queries for millisecond-level retrieval
- Efficient schema with 245+ records within minutes

### 📊 **Interactive Dashboard**
- Real-time price updates with 3-second refresh
- 4 interactive tabs: Overview, Charts, Data Table, Analytics
- Plotly visualizations with time-range selectors
- CSV export functionality
- System health monitoring

### 🐳 **Full Containerization**
- 9 Docker containers orchestrated with Docker Compose
- One-command deployment: `docker-compose up -d`
- Health checks and automatic restarts
- Volume persistence for data durability

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Source** | Finnhub API | Live stock market data |
| **Message Queue** | Apache Kafka 7.5.0 | Distributed streaming platform |
| **Stream Processing** | Apache Spark 3.5.0 | Real-time data processing |
| **Storage** | PostgreSQL 16 | Time-series data storage |
| **Cache** | Redis 7 | Hot data caching |
| **Visualization** | Streamlit 1.29.0 | Interactive dashboard |
| **Orchestration** | Docker Compose | Container management |
| **Monitoring** | Kafka UI, pgAdmin | System monitoring |

**Languages:** Python 3.11  
**Architecture:** Mac M2 (ARM64) compatible

---

## 📦 Project Structure
```
realtime-stock-pipeline/
├── src/
│   ├── producer/
│   │   └── stock_producer.py          # Finnhub → Kafka producer
│   ├── processing/
│   │   └── spark_processor_with_storage.py  # Spark streaming job
│   ├── storage/
│   │   └── database.py                # PostgreSQL & Redis clients
│   ├── dashboard/
│   │   └── app.py                     # Streamlit dashboard
│   └── utils/
│       └── logger.py                  # Logging configuration
├── config/
│   ├── kafka_config.py                # Kafka settings
│   ├── spark_config.py                # Spark settings
│   └── db_config.py                   # Database settings
├── scripts/
│   └── init_db.sql                    # PostgreSQL schema
├── tests/
│   ├── test_producer.py               # Producer unit tests
│   ├── test_kafka.py                  # Kafka integration tests
│   └── test_postgres.py               # Database tests
├── docker-compose.yml                 # Container orchestration
├── Dockerfile.producer                # Producer container
├── Dockerfile.spark                   # Spark container
├── Dockerfile.dashboard               # Dashboard container
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop 4.0+
- 8GB+ RAM
- 10GB+ free disk space
- Finnhub API Key (free at [finnhub.io](https://finnhub.io))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/RahulSunny1209/realtime-stock-pipeline.git
cd realtime-stock-pipeline
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your Finnhub API key
```

3. **Start the pipeline**
```bash
docker-compose up -d
```

4. **Access the dashboard**
```bash
open http://localhost:8501
```

### Access Points
- **Dashboard:** http://localhost:8501
- **Kafka UI:** http://localhost:8080
- **pgAdmin:** http://localhost:5050 (admin@stock.com / admin)

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Data Latency** | < 30 seconds (producer → dashboard) |
| **Processing Throughput** | 1-5 records/second per stock |
| **Storage Efficiency** | ~245 records in first 5 minutes |
| **Dashboard Refresh** | 3-second intervals |
| **Kafka Partitions** | 3 (for parallel processing) |
| **Spark Batch Interval** | 30 seconds |
| **Uptime** | 99.9% (with auto-restart) |

---

## 🧪 Testing

Run the complete test suite:
```bash
# Activate virtual environment
source venv/bin/activate

# Test producer → Kafka
python tests/test_producer.py

# Test Kafka messages
python tests/test_kafka.py

# Test PostgreSQL storage
python tests/test_postgres.py

# Test complete pipeline
python tests/test_complete_pipeline.py
```

---

## 📈 Dashboard Features

### Overview Tab
- Live stock prices for all 5 stocks
- High/Low prices for the day
- Volume indicators (N/A for Finnhub limitation)
- Last update timestamps

### Charts Tab
- Interactive Plotly line charts
- Time range selectors (1h, 6h, 24h)
- Multi-stock comparison
- Hover tooltips with details

### Data Table Tab
- Historical data with all fields
- Filter by stock symbol
- Adjustable record limit (10-100)
- CSV export functionality

### Analytics Tab
- Summary statistics (avg, min, max, std dev)
- Price comparison chart across stocks
- Record counts per symbol

---

## 🔧 Configuration

### Producer Settings (.env)
```bash
FINNHUB_API_KEY=your_key_here
FETCH_INTERVAL=30        # Seconds between fetches
SYMBOL_DELAY=3           # Seconds between symbols
STOCK_SYMBOLS=AAPL,GOOGL,MSFT,AMZN,TSLA
```

### Kafka Settings
- Bootstrap Servers: `kafka:29092`
- Topic: `stock-prices`
- Partitions: 3
- Replication Factor: 1

### Spark Settings
- Trigger Interval: 30 seconds
- Checkpoint Directory: `/app/checkpoints`
- Shuffle Partitions: 2

---

## 🐛 Troubleshooting

### Producer not sending data
```bash
# Check producer logs
docker-compose logs producer --tail=20

# Verify Finnhub API key
echo $FINNHUB_API_KEY
```

### Spark not processing
```bash
# Check Spark logs
docker-compose logs spark-processor --tail=50

# Verify Kafka topic exists
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Dashboard not showing data
```bash
# Check PostgreSQL records
docker exec postgres psql -U stockuser -d stockmarket -c "SELECT COUNT(*) FROM stock_prices;"

# Restart dashboard
docker-compose restart dashboard
```

### Complete system reset
```bash
# Stop everything and remove volumes
docker-compose down -v

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

---

## 📚 Learning Resources

### Blog Series (Coming Soon)
1. **Part 1:** Setting up a Real-Time Data Pipeline on Mac M2
2. **Part 2:** Building a Kafka Producer with Finnhub API
3. **Part 3:** Stream Processing with Apache Spark
4. **Part 4:** PostgreSQL and Redis for Data Storage
5. **Part 5:** Creating an Interactive Dashboard with Streamlit
6. **Part 6:** Containerizing a Data Pipeline with Docker
7. **Part 7:** Deploying to AWS Cloud

### Key Concepts Demonstrated
- Real-time data streaming
- Apache Kafka publish-subscribe model
- Spark Structured Streaming
- Micro-batch processing
- Time-series data modeling
- Docker containerization
- Service orchestration
- Data visualization

---

## 🎯 Future Enhancements

- [ ] Add real-time alerts (price thresholds)
- [ ] Implement technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Add ML price predictions with TensorFlow
- [ ] Expand to 50+ stocks
- [ ] Add sentiment analysis from news APIs
- [ ] Implement Kubernetes deployment
- [ ] Add Grafana monitoring dashboards
- [ ] Create REST API endpoints

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

---

## 👤 Author

**Your Name**
- GitHub: [Rahul](https://github.com/RahulSunny1209)
- LinkedIn: [Kothagundla Rahul](https://linkedin.com/in/kothagundlarahul)
- Portfolio: [Kothagundla Rahul](https://medium.com/@kothagundlarahul)

---

## 🙏 Acknowledgments

- [Finnhub API](https://finnhub.io) for free stock market data
- [Apache Kafka](https://kafka.apache.org) for distributed streaming
- [Apache Spark](https://spark.apache.org) for stream processing
- [Streamlit](https://streamlit.io) for rapid dashboard development

---

## 📊 Project Status

**Current Phase:** Phase 6 Complete - Full Containerization ✅  
**Next Phase:** Phase 7 - AWS Cloud Deployment  
**Overall Progress:** 75% Complete

---

**⭐ If you found this project helpful, please give it a star!**
