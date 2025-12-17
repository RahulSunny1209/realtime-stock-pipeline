"""
Stock Data Producer - Production Version
Fetches live stock data from Polygon.io and sends to Kafka
"""

import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError
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
        """
        Safely read an integer environment variable.
        Falls back to default if missing or invalid.
        """
        value = os.getenv(key)
        try:
            return int(value) if value is not None else default
        except ValueError:
            logger.warning(f"⚠️ Invalid int for {key}: {value}. Using default {default}")
            return default  

# Get configuration from environment
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
FETCH_INTERVAL = get_int_env("FETCH_INTERVAL", 60)
RETRY_ATTEMPTS = get_int_env("RETRY_ATTEMPTS", 3)
SYMBOL_DELAY = get_int_env("SYMBOL_DELAY", 3)
METADATA_TTL_HOURS = get_int_env("METADATA_TTL_HOURS", 6)

# Validate API key
if not POLYGON_API_KEY:
    logger.error("❌ POLYGON_API_KEY not found in environment variables")
    logger.error("Please set POLYGON_API_KEY in .env file")
    sys.exit(1)


class StockProducer:
    """Produces real-time stock data to Kafka with production-grade features"""
    
    def __init__(self, symbols: List[str]):
        """
        Initialize stock producer
        
        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'GOOGL'])
        """
        self.symbols = symbols
        self.producer: Optional[KafkaProducer] = None
        self.topic = kafka_config.STOCK_TOPIC
        
        # Metadata caching
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}
        self.metadata_last_updated: Dict[str, float] = {}
        self.METADATA_TTL_SECONDS = METADATA_TTL_HOURS * 60 * 60
        
        # HTTP session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "RealTimeStockPipeline/1.0"
        })
        
        # Metrics tracking
        self.metrics = {
            'messages_sent': 0,
            'messages_failed': 0,
            'total_iterations': 0,
            'api_calls': 0,
            'cache_hits': 0,
            'start_time': time.time()
        }
        
        logger.info(f"Initializing StockProducer for symbols: {symbols}")
        logger.info(f"Fetch interval: {FETCH_INTERVAL}s, Symbol delay: {SYMBOL_DELAY}s")
        
    def connect(self) -> bool:
        """Connect to Kafka broker"""
        try:
            producer_config = kafka_config.get_producer_config()
            
            # Add serializers
            producer_config['value_serializer'] = lambda v: json.dumps(v).encode('utf-8')
            producer_config['key_serializer'] = lambda k: k.encode('utf-8') if k else None
            
            self.producer = KafkaProducer(**producer_config)
            logger.info(f"✅ Connected to Kafka at {producer_config['bootstrap_servers']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            return False
    
    def fetch_metadata(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch and cache stock metadata
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with metadata
        """
        # Check cache first
        if (
            symbol in self.metadata_cache
            and time.time() - self.metadata_last_updated.get(symbol, 0) < self.METADATA_TTL_SECONDS
        ):
            self.metrics['cache_hits'] += 1
            logger.debug(f"📦 Cache hit for {symbol} metadata")
            return self.metadata_cache[symbol]
        
        # Fetch from API
        try:
            self.metrics['api_calls'] += 1
            details_url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
            details_resp = self.session.get(
                details_url,
                params={"apiKey": POLYGON_API_KEY},
                timeout=10
            )
            details_resp.raise_for_status()
            details = details_resp.json()["results"]
            
            # Cache the metadata
            self.metadata_cache[symbol] = {
                "market_cap": details.get("market_cap", 0),
                "company_name": details.get("name", symbol),
                "fifty_two_week_high": details.get("high_52_week", 0),
                "fifty_two_week_low": details.get("low_52_week", 0),
            }
            self.metadata_last_updated[symbol] = time.time()
            
            logger.info(f"📥 Fetched and cached metadata for {symbol}")
            return self.metadata_cache[symbol]
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch metadata for {symbol}: {e}")
            # Return default values if metadata fetch fails
            return {
                "market_cap": 0,
                "company_name": symbol,
                "fifty_two_week_high": 0,
                "fifty_two_week_low": 0,
            }
    
    def fetch_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current stock data from Polygon.io
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with stock data or None if failed
        """
        try:
            self.metrics['api_calls'] += 1
            
            # Fetch daily aggregates (previous day's data)
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            resp = self.session.get(
                url,
                params={"apiKey": POLYGON_API_KEY},
                timeout=10
            )
            resp.raise_for_status()
            
            data = resp.json()
            
            if "results" not in data or not data["results"]:
                logger.warning(f"⚠️  No data returned for {symbol}")
                return None
            
            agg = data["results"][0]
            
            # Get metadata (from cache or API)
            meta = self.fetch_metadata(symbol)
            
            # Build stock data
            stock_data = {
                "symbol": symbol,
                "price": agg["c"],  # Close price
                "volume": agg["v"],
                "market_cap": meta["market_cap"],
                "day_high": agg["h"],
                "day_low": agg["l"],
                "fifty_two_week_high": meta["fifty_two_week_high"],
                "fifty_two_week_low": meta["fifty_two_week_low"],
                "timestamp": datetime.utcnow().isoformat(),
                "company_name": meta["company_name"],
                "open": agg["o"],
                "vwap": agg.get("vw", 0),  # Volume weighted average price
            }
            
            logger.info(f"📊 Fetched {symbol}: ${stock_data['price']:.2f}")
            return stock_data
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Timeout fetching {symbol}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"🌐 HTTP error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol}: {e}")
            return None
    
    def fetch_with_retry(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch stock data with exponential backoff retry
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock data or None
        """
        for attempt in range(RETRY_ATTEMPTS):
            try:
                data = self.fetch_stock_data(symbol)
                if data:
                    return data
                
                # If no data but no exception, don't retry
                logger.warning(f"⚠️  No data for {symbol}, skipping")
                return None
                
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"⚠️  Attempt {attempt + 1}/{RETRY_ATTEMPTS} failed for {symbol}: {e}")
                
                if attempt < RETRY_ATTEMPTS - 1:
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All retries exhausted for {symbol}")
                    self.metrics['messages_failed'] += 1
                    return None
    
    def send_to_kafka(self, data: Dict[str, Any]) -> bool:
        """
        Send stock data to Kafka
        
        Args:
            data: Stock data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not data:
            return False
        
        if not self.producer:
            logger.error("❌ Kafka producer not initialized")
            return False
        
        try:
            # Send message
            future = self.producer.send(
                self.topic,
                key=data['symbol'],
                value=data
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            self.metrics['messages_sent'] += 1
            
            logger.info(
                f"✅ Sent {data['symbol']} to topic '{record_metadata.topic}' "
                f"partition {record_metadata.partition} offset {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logger.error(f"❌ Kafka error: {e}")
            self.metrics['messages_failed'] += 1
            return False
        except Exception as e:
            logger.error(f"❌ Error sending to Kafka: {e}")
            self.metrics['messages_failed'] += 1
            return False
    
    def print_metrics(self):
        """Print performance metrics"""
        runtime = time.time() - self.metrics['start_time']
        runtime_minutes = runtime / 60
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 PIPELINE METRICS")
        logger.info(f"{'='*60}")
        logger.info(f"Runtime: {runtime_minutes:.1f} minutes ({runtime:.0f}s)")
        logger.info(f"Iterations: {self.metrics['total_iterations']}")
        logger.info(f"Messages Sent: {self.metrics['messages_sent']}")
        logger.info(f"Messages Failed: {self.metrics['messages_failed']}")
        
        total_messages = self.metrics['messages_sent'] + self.metrics['messages_failed']
        if total_messages > 0:
            success_rate = (self.metrics['messages_sent'] / total_messages) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info(f"API Calls: {self.metrics['api_calls']}")
        logger.info(f"Cache Hits: {self.metrics['cache_hits']}")
        
        if self.metrics['api_calls'] > 0:
            cache_hit_rate = (self.metrics['cache_hits'] / (self.metrics['api_calls'] + self.metrics['cache_hits'])) * 100
            logger.info(f"Cache Hit Rate: {cache_hit_rate:.1f}%")
        
        logger.info(f"{'='*60}\n")
    
    def produce(self, interval: Optional[int] = None):
        """
        Start producing stock data
        
        Args:
            interval: Fetch interval in seconds (uses env var if not provided)
        """
        if interval is None:
            interval = FETCH_INTERVAL
        
        if not self.producer:
            if not self.connect():
                logger.error("Cannot start producing - connection failed")
                return
        
        logger.info(f"🚀 Starting producer - fetching every {interval} seconds")
        logger.info(f"📈 Monitoring stocks: {', '.join(self.symbols)}")
        logger.info(f"📡 Topic: {self.topic}")
        logger.info(f"🔄 Retry attempts: {RETRY_ATTEMPTS}")
        logger.info(f"⏱️  Symbol delay: {SYMBOL_DELAY}s")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.metrics['total_iterations'] += 1
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration #{self.metrics['total_iterations']} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Fetch and send data for each symbol
                for symbol in self.symbols:
                    data = self.fetch_with_retry(symbol)
                    if data:
                        self.send_to_kafka(data)
                    time.sleep(SYMBOL_DELAY)  # Delay between symbols
                
                # Print metrics every 10 iterations
                if self.metrics['total_iterations'] % 10 == 0:
                    self.print_metrics()
                
                logger.info(f"\n⏳ Waiting {interval} seconds until next fetch...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping producer...")
            self.print_metrics()
            self.close()
        except Exception as e:
            logger.error(f"❌ Producer error: {e}")
            self.print_metrics()
            self.close()
    
    def close(self):
        """Close connections and cleanup"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("✅ Producer closed successfully")
        
        if self.session:
            self.session.close()
            logger.info("✅ HTTP session closed")


def main():
    """Main function"""
    # Get symbols from environment or use default
    symbols_str = os.getenv("STOCK_SYMBOLS", "AAPL,GOOGL,MSFT,AMZN,TSLA")
    symbols = [s.strip() for s in symbols_str.split(",")]
    
    logger.info("╔════════════════════════════════════════════════╗")
    logger.info("║   REAL-TIME STOCK MARKET DATA PIPELINE        ║")
    logger.info("║   Producer: Polygon.io → Kafka                ║")
    logger.info("╚════════════════════════════════════════════════╝\n")
    
    # Create and start producer
    producer = StockProducer(symbols)
    producer.produce()


if __name__ == '__main__':
    main()
