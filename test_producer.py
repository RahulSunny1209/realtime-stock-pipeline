"""
Test: Producer sends data to Kafka
"""

import sys
sys.path.append('.')

from kafka import KafkaProducer
import json
import requests
import time
import os

print("=" * 60)
print("TEST 1: PRODUCER → KAFKA")
print("=" * 60)
print()

# Test 1: Can we connect to Kafka?
print("1️⃣ Testing Kafka Connection...")
try:
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("✅ Connected to Kafka at localhost:9092")
except Exception as e:
    print(f"❌ Failed to connect to Kafka: {e}")
    sys.exit(1)

# Test 2: Can we fetch stock data from Finnhub?
print("\n2️⃣ Testing Finnhub API...")
API_KEY = os.getenv('FINNHUB_API_KEY', 'csusv69r01qopaulvba0csusv69r01qopaulvbag')
url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={API_KEY}"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if 'c' in data and data['c'] > 0:
        print(f"✅ Successfully fetched AAPL data")
        print(f"   Price: ${data['c']}")
        print(f"   High: ${data['h']}")
        print(f"   Low: ${data['l']}")
        
        # Create message for Kafka
        message = {
            'symbol': 'AAPL',
            'price': data['c'],
            'high': data['h'],
            'low': data['l'],
            'open': data['o'],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        print(f"❌ Invalid data from Finnhub: {data}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Failed to fetch from Finnhub: {e}")
    sys.exit(1)

# Test 3: Can we send to Kafka?
print("\n3️⃣ Testing Send to Kafka...")
try:
    future = producer.send('stock-prices', key=b'AAPL', value=message)
    result = future.get(timeout=10)
    print("✅ Successfully sent message to Kafka")
    print(f"   Topic: stock-prices")
    print(f"   Partition: {result.partition}")
    print(f"   Offset: {result.offset}")
except Exception as e:
    print(f"❌ Failed to send to Kafka: {e}")
    sys.exit(1)

producer.close()

print("\n" + "=" * 60)
print("✅ PRODUCER TEST PASSED!")
print("=" * 60)
