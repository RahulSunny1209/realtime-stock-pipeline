"""
Test: Verify messages exist in Kafka
"""

from kafka import KafkaConsumer
import json
import sys

print("=" * 60)
print("TEST 2: KAFKA MESSAGE VERIFICATION")
print("=" * 60)
print()

try:
    consumer = KafkaConsumer(
        'stock-prices',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=5000
    )
    
    print("✅ Connected to Kafka")
    print("📊 Reading messages from 'stock-prices' topic...\n")
    
    message_count = 0
    for message in consumer:
        message_count += 1
        data = message.value
        
        print(f"Message #{message_count}:")
        print(f"  Symbol: {data.get('symbol')}")
        print(f"  Price: ${data.get('price')}")
        print(f"  Timestamp: {data.get('timestamp') or data.get('event_time')}")
        print(f"  Partition: {message.partition}, Offset: {message.offset}")
        print()
        
        if message_count >= 5:  # Show first 5 messages
            break
    
    if message_count > 0:
        print("=" * 60)
        print(f"✅ KAFKA TEST PASSED! Found {message_count} messages")
        print("=" * 60)
    else:
        print("⚠️  No messages found in Kafka")
        print("   The producer container may not be running")
        print("   Check: docker-compose logs stock-producer")
    
    consumer.close()
    
except Exception as e:
    print(f"❌ Kafka test failed: {e}")
    sys.exit(1)
