# Building a Production-Ready Kafka Producer: From Yahoo Finance to Polygon.io

## Article Metadata
- **Estimated Reading Time**: 8-10 minutes
- **Tags**: #DataEngineering #Kafka #Python #RealTime #StockMarket
- **Series**: Real-Time Stock Pipeline (Part 2 of 8)

---

## 1. Introduction (1-2 min)

### Hook
"The first API call returned 200 OK. The second one failed silently. This is the story of why free APIs can be your worst nightmare in production."

### Context
- In Part 1, we set up our development environment
- Now we're building the data ingestion layer
- Learned a hard lesson about choosing the right API

---

## 2. The Yahoo Finance Problem (2-3 min)

### Initial Approach
```python
ticker = yf.Ticker("AAPL")
info = ticker.info  # This worked... until it didn't
```

### What Went Wrong
- Error: "Expecting value: line 1 column 1"
- `ticker.info` is NOT for real-time polling
- Yahoo Finance rate-limits aggressively
- No official documentation
- Unreliable for production systems

### Screenshot
[Include terminal showing Yahoo Finance errors]

### The Moment of Realization
"This is an undocumented web scraping target, not a production API."

---

## 3. Migration to Polygon.io (2-3 min)

### Why Polygon.io?
1. **Official Market Data API** - Legitimate data source
2. **Clear Documentation** - Know exactly what you're getting
3. **Predictable Rate Limits** - 5 calls/minute on free tier
4. **Production-Ready** - Used by real applications

### The Switch
```python
# Before: Yahoo Finance
ticker = yf.Ticker("AAPL")
price = ticker.info['regularMarketPrice']

# After: Polygon.io
url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
resp = requests.get(url, params={"apiKey": API_KEY})
price = resp.json()["results"][0]["c"]
```

### Free Tier Considerations
- 5 API calls per minute
- Daily aggregates (no real-time ticks)
- Perfect for learning projects

---

## 4. Smart Caching Strategy (2-3 min)

### The Problem
Fetching metadata (company name, market cap) every 60 seconds = wasteful

### The Solution: TTL-Based Caching
```python
# Cache metadata for 6 hours
METADATA_TTL = 6 * 60 * 60  # Company info rarely changes

if symbol not in cache or time.time() - last_updated > TTL:
    # Fetch from API
    cache[symbol] = fetch_metadata(symbol)
```

### Impact
- **Before**: 10 API calls per minute (2 per symbol × 5 symbols)
- **After**: ~2 API calls per minute (only price data)
- **Savings**: 80% reduction in API calls

### Metrics
```
API Calls: 120
Cache Hits: 480
Cache Hit Rate: 80%
```

---

## 5. Production Features (2-3 min)

### Retry Logic with Exponential Backoff
```python
for attempt in range(3):
    try:
        return fetch_data(symbol)
    except Exception:
        wait = 2 ** attempt  # 1s, 2s, 4s
        time.sleep(wait)
```

### Environment Variables
```bash
# .env file
POLYGON_API_KEY=your_key_here
FETCH_INTERVAL=60
RETRY_ATTEMPTS=3
```

### Metrics Tracking
```python
metrics = {
    'messages_sent': 0,
    'messages_failed': 0,
    'success_rate': 0,
    'cache_hit_rate': 0
}
```

### Screenshot
[Include metrics output showing 100% success rate]

---

## 6. Kafka Integration (1-2 min)

### Producer Configuration
```python
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',  # Wait for all replicas
    retries=3,
    compression_type='gzip'
)
```

### Sending Messages
```python
future = producer.send(
    'stock-prices',
    key=symbol,
    value=stock_data
)
record_metadata = future.get(timeout=10)
```

### Kafka UI
[Screenshot of Kafka UI showing messages in stock-prices topic]

---

## 7. Testing & Verification (1-2 min)

### Two-Terminal Setup
**Terminal 1**: Consumer (listening)
```bash
python src/consumer/stock_consumer.py
```

**Terminal 2**: Producer (sending)
```bash
python src/producer/stock_producer.py
```

### Output
```
Producer:
✅ Sent AAPL to topic 'stock-prices' partition 0 offset 5

Consumer:
Symbol: AAPL
Price: $274.61
Volume: 37,648,586
```

---

## 8. Key Lessons Learned (1-2 min)

### Technical Lessons
1. **Validate API entitlements**, not just credentials
2. **Cache aggressively** for rate-limited APIs
3. **Retry with backoff** for resilience
4. **Track metrics** for observability

### Design Principles
- Choose official APIs over web scraping
- Design for rate limits from day one
- Make configuration external (env vars)
- Add observability early

### Interview Talking Points
> "I migrated from Yahoo Finance to Polygon.io because Yahoo Finance is an undocumented scraping target unsuitable for production. Polygon.io provides a proper market data API with clear documentation, predictable rate limits, and guaranteed reliability."

---

## 9. What's Next (1 min)

### Phase 3 Preview
- Apache Spark for stream processing
- Calculate moving averages
- Technical indicators (RSI, MACD)
- Real-time analytics

### Call to Action
- GitHub: [Link to repo]
- Try it yourself: Fork and run
- Follow for Phase 3: Spark processing

---

## Code Snippets to Include

1. Yahoo Finance error
2. Polygon.io API call
3. Caching logic
4. Retry mechanism
5. Kafka producer setup
6. Metrics dashboard

## Screenshots to Take

1. Yahoo Finance error in terminal
2. Successful Polygon.io fetch
3. Metrics after 10 iterations
4. Kafka UI with messages
5. Producer and consumer side-by-side
6. Architecture diagram

## SEO Keywords
- Real-time data pipeline
- Kafka producer Python
- Stock market data
- Polygon.io API
- Yahoo Finance alternative
- Data engineering portfolio
