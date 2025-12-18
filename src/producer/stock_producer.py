"""
Stock Data Producer - Finnhub Edition (Free & Real-Time)
Fetches live stock data using Finnhub API (60 calls/min limit)
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from kafka import KafkaProducer
import sys 
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append('.')

from src.utils.logger import setup_logger
from config.kafka_config import kafka_config

# Setup logger
logger = setup_logger(__name__, 'logs/producer.log')

def get_int_env(key: str, default: int) -> int:
    value = os.getenv(key)
    try:
        return int(value) if value is not None else default
    except ValueError:
        logger.warning(f"⚠️ Invalid int for {key}: {value}. Using default {default}")
        return default  

# CONFIGURATION
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FETCH_INTERVAL = get_int_env("FETCH_INTERVAL", 30)
SYMBOL_DELAY = get_int_env("SYMBOL_DELAY", 1) # Faster delay to fit free tier limits

# Validate Key
if not FINNHUB_API_KEY:
    logger.error("❌ FINNHUB_API_KEY not found in .env file")
    sys.exit(1)
 
class StockProducer:
    """Produces real-time stock data to Kafka using Finnhub"""
     
    def __init__(self, symbols: List[str]): 
        self.symbols = symbols
        self.producer: Optional[KafkaProducer] = None
        self.topic = kafka_config.STOCK_TOPIC
        
        # Finnhub Free Tier Limit: 60 calls/minute
        # We must be careful not to exceed this.
        self.metrics = {
            'messages_sent': 0, 'messages_failed': 0, 'total_iterations': 0,
            'api_calls': 0, 'start_time': time.time()
        }
        
        logger.info(f"Initializing Finnhub Producer for: {symbols}")
        logger.info(f"Fetch interval: {FETCH_INTERVAL}s")
        
    def connect(self) -> bool:
        try: 
            producer_config = kafka_config.get_producer_config() 
            producer_config['value_serializer'] = lambda v: json.dumps(v).encode('utf-8')
            producer_config['key_serializer'] = lambda k: k.encode('utf-8') if k else None
            
            self.producer = KafkaProducer(**producer_config)
            logger.info(f"✅ Connected to Kafka at {producer_config['bootstrap_servers']}")
            return True
        except Exception as e: 
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            return False
    
    def fetch_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]: 
        """
        Fetch LIVE data from Finnhub Quote Endpoint.
        Docs: https://finnhub.io/docs/api/quote
        """
        try:
            self.metrics['api_calls'] += 1
            
            # Finnhub Quote Endpoint
            url = "https://finnhub.io/api/v1/quote"
            params = {
                "symbol": symbol,
                "token": FINNHUB_API_KEY
            }
            
            # Standard requests call (lightweight)
            resp = requests.get(url, params=params, timeout=10)
            
            if resp.status_code == 429:
                logger.warning(f"⚠️ Rate limit exceeded for {symbol} (Free tier: 60/min)")
                return None
            
            resp.raise_for_status() 
            data = resp.json()
            
            # Check if data is valid (Finnhub returns 0s for invalid symbols)
            if data.get('c', 0) == 0 and data.get('h', 0) == 0:
                logger.warning(f"⚠️ No data found for {symbol}")
                return None

            # Finnhub Response Mapping:
            # c = Current Price
            # h = High
            # l = Low
            # o = Open
            # pc = Previous Close
            # t = Timestamp
            
            stock_data = {
                "symbol": symbol,
                "price": float(data['c']),
                "volume": 0, # Note: Finnhub basic Quote API doesn't send volume. 
                             # If you strictly need volume, we can add a 'dummy' or fetch separately.
                             # For now, we set 0 to keep it fast/free.
                "market_cap": 0, # Not in Quote endpoint
                "day_high": float(data['h']),
                "day_low": float(data['l']),
                "fifty_two_week_high": 0, # Not in Quote endpoint
                "fifty_two_week_low": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "company_name": symbol,
                "open": float(data['o']),
                "vwap": float(data['c']), # Approx
                "source": "Finnhub"
            }
            
            logger.info(f"📊 Fetched {symbol}: ${stock_data['price']:.2f} (Live)")
            return stock_data
             
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol}: {e}")
            return None
    
    def send_to_kafka(self, data: Dict[str, Any]) -> bool:
        if not data or not self.producer: return False
        try:
            future = self.producer.send(self.topic, key=data['symbol'], value=data)
            future.get(timeout=10)
            self.metrics['messages_sent'] += 1
            logger.info(f"✅ Sent {data['symbol']} -> Kafka")
            return True
        except Exception as e: 
            logger.error(f"❌ Kafka Error: {e}")
            self.metrics['messages_failed'] += 1
            return False
    
    def produce(self):
        if not self.producer and not self.connect(): return
        
        logger.info(f"🚀 Producer Started (Finnhub Source)")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.metrics['total_iterations'] += 1
                logger.info(f"\n--- Iteration #{self.metrics['total_iterations']} ---")
                
                for symbol in self.symbols: 
                    data = self.fetch_stock_data(symbol)
                    if data: self.send_to_kafka(data)
                    # Small delay to ensure we don't burst limits
                    time.sleep(SYMBOL_DELAY) 
                
                logger.info(f"\n\t\t⏳ Waiting {FETCH_INTERVAL}s...")
                time.sleep(FETCH_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping...")
            if self.producer: self.producer.close()

if __name__ == '__main__':
    symbols_env = os.getenv("STOCK_SYMBOLS", "AAPL,GOOGL,MSFT,AMZN,TSLA")
    producer = StockProducer([s.strip() for s in symbols_env.split(",")])
    producer.produce()