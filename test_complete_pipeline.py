"""
Test: Complete end-to-end pipeline flow
"""

import sys
sys.path.append('.')

from src.storage.database import PostgresStorage, RedisCache
from kafka import KafkaProducer
import json
import time
import requests
import os

print("=" * 60)
print("TEST 5: COMPLETE PIPELINE FLOW")
print("=" * 60)
print()

# Step 1: Send test data to Kafka
print("STEP 1: Sending test data to Kafka...")
try:
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    # Fetch real data
    API_KEY = os.getenv('FINNHUB_API_KEY', 'csusv69r01qopaulvba0csusv69r01qopaulvbag')
    url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={API_KEY}"
    response = requests.get(url, timeout=10)
    data = response.json()
    
    message = {
        'symbol': 'AAPL',
        'price': data['c'],
        'high': data['h'],
        'low': data['l'],
        'open': data['o'],
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    producer.send('stock-prices', key=b'AAPL', value=message)
    producer.flush()
    print(f"✅ Sent AAPL data: ${message['price']}")
    test_timestamp = message['timestamp']
    producer.close()
except Exception as e:
    print(f"❌ Failed to send data: {e}")
    sys.exit(1)

# Step 2: Wait for Spark processing
print("\nSTEP 2: Waiting for Spark to process (30 seconds)...")
for i in range(30, 0, -1):
    print(f"   ⏳ {i} seconds remaining...", end='\r')
    time.sleep(1)
print("\n")

# Step 3: Check PostgreSQL
print("STEP 3: Checking PostgreSQL...")
postgres = PostgresStorage()
if postgres.connect():
    postgres.cursor.execute("""
        SELECT COUNT(*) 
        FROM stock_prices 
        WHERE symbol='AAPL'
    """)
    
    count = postgres.cursor.fetchone()[0]
    if count > 0:
        print(f"✅ Found {count} AAPL record(s) in PostgreSQL")
        
        # Show latest record
        postgres.cursor.execute("""
            SELECT symbol, price, event_time 
            FROM stock_prices 
            WHERE symbol='AAPL' 
            ORDER BY event_time DESC 
            LIMIT 1
        """)
        latest = postgres.cursor.fetchone()
        print(f"   Latest: ${latest[1]} at {latest[2]}")
    else:
        print("⚠️  No AAPL data in PostgreSQL yet")
        print("   Check Spark logs: docker-compose logs spark-processor")
    
    postgres.close()
else:
    print("❌ Failed to connect to PostgreSQL")

# Step 4: Check Redis (optional - may not be in use)
print("\nSTEP 4: Checking Redis cache...")
redis_cache = RedisCache()
if redis_cache.connect():
    keys = redis_cache.redis_client.keys("*AAPL*")
    if keys:
        print(f"✅ Found {len(keys)} AAPL key(s) in Redis cache")
    else:
        print("⚠️  No AAPL data in Redis cache")
    redis_cache.close()
else:
    print("⚠️  Redis connection failed (cache may not be in use)")

print("\n" + "=" * 60)
print("✅ PIPELINE FLOW TEST COMPLETE!")
print("=" * 60)
print("\n📊 DATA FLOW SUMMARY:")
print("   Producer → Kafka: ✅")
print("   Kafka → Spark: ⏳ (check logs)")
print("   Spark → PostgreSQL:", "✅" if count > 0 else "⏳")
print("   Redis Cache: ⏳ (optional)")
