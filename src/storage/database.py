"""
Database Storage Layer
Handles PostgreSQL and Redis operations
"""

import psycopg2
from psycopg2.extras import execute_batch
import redis
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
sys.path.append('.')

from src.utils.logger import setup_logger
from config.db_config import db_config

# Setup logger
logger = setup_logger(__name__, 'logs/database.log')


class PostgresStorage:
    """PostgreSQL storage operations"""
    
    def __init__(self):
        """Initialize PostgreSQL connection"""
        self.conn = None
        self.cursor = None
        logger.info("Initializing PostgreSQL storage")
    
    def connect(self) -> bool:
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(db_config.get_postgres_url())
            self.cursor = self.conn.cursor()
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
    
    def insert_stock_price(self, data: Dict[str, Any]) -> bool:
        """Insert single stock price record"""
        try:
            query = """
                INSERT INTO stock_prices 
                (symbol, price, volume, market_cap, day_high, day_low, 
                 open_price, vwap, company_name, source, event_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, event_time) DO NOTHING
            """
            
            values = (
                data['symbol'],
                data['price'],
                data.get('volume', 0),
                data.get('market_cap', 0),
                data.get('day_high', 0),
                data.get('day_low', 0),
                data.get('open', 0),
                data.get('vwap', 0),
                data.get('company_name', data['symbol']),
                data.get('source', 'Finnhub'),
                data['timestamp']
            )
            
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.info(f"✅ Inserted {data['symbol']} at {data['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to insert stock price: {e}")
            self.conn.rollback()
            return False
    
    def insert_batch_stock_prices(self, data_list: List[Dict[str, Any]]) -> int:
        """Insert multiple stock price records"""
        try:
            query = """
                INSERT INTO stock_prices 
                (symbol, price, volume, market_cap, day_high, day_low, 
                 open_price, vwap, company_name, source, event_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, event_time) DO NOTHING
            """
            
            values_list = [
                (
                    data['symbol'],
                    data['price'],
                    data.get('volume', 0),
                    data.get('market_cap', 0),
                    data.get('day_high', 0),
                    data.get('day_low', 0),
                    data.get('open', 0),
                    data.get('vwap', 0),
                    data.get('company_name', data['symbol']),
                    data.get('source', 'Finnhub'),
                    data['timestamp']
                )
                for data in data_list
            ]
            
            execute_batch(self.cursor, query, values_list)
            self.conn.commit()
            
            logger.info(f"✅ Batch inserted {len(data_list)} records")
            return len(data_list)
            
        except Exception as e:
            logger.error(f"❌ Failed to insert batch: {e}")
            self.conn.rollback()
            return 0
    
    def insert_moving_average(self, data: Dict[str, Any]) -> bool:
        """Insert moving average record"""
        try:
            query = """
                INSERT INTO stock_moving_averages
                (symbol, window_start, window_end, avg_price_5min, 
                 max_price_5min, min_price_5min, total_volume_5min, num_updates)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, window_start, window_end) 
                DO UPDATE SET 
                    avg_price_5min = EXCLUDED.avg_price_5min,
                    max_price_5min = EXCLUDED.max_price_5min,
                    min_price_5min = EXCLUDED.min_price_5min,
                    total_volume_5min = EXCLUDED.total_volume_5min,
                    num_updates = EXCLUDED.num_updates,
                    calculation_time = CURRENT_TIMESTAMP
            """
            
            values = (
                data['symbol'],
                data['window_start'],
                data['window_end'],
                data['avg_price_5min'],
                data['max_price_5min'],
                data['min_price_5min'],
                data['total_volume_5min'],
                data['num_updates_5min']
            )
            
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.info(f"✅ Inserted moving avg for {data['symbol']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to insert moving average: {e}")
            self.conn.rollback()
            return False
    
    def get_latest_prices(self, limit: int = 10) -> List[Dict]:
        """Get latest stock prices"""
        try:
            query = """
                SELECT * FROM latest_stock_prices
                ORDER BY event_time DESC
                LIMIT %s
            """
            self.cursor.execute(query, (limit,))
            columns = [desc[0] for desc in self.cursor.description]
            results = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"❌ Failed to get latest prices: {e}")
            return []
    
    def get_symbol_history(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get price history for a symbol"""
        try:
            query = """
                SELECT symbol, price, volume, event_time
                FROM stock_prices
                WHERE symbol = %s 
                  AND event_time >= NOW() - INTERVAL '%s hours'
                ORDER BY event_time DESC
            """
            self.cursor.execute(query, (symbol, hours))
            columns = [desc[0] for desc in self.cursor.description]
            results = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"❌ Failed to get symbol history: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("✅ PostgreSQL connection closed")


class RedisCache:
    """Redis caching operations"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = None
        logger.info("Initializing Redis cache")
    
    def connect(self) -> bool:
        """Connect to Redis"""
        try:
            config = db_config.get_redis_config()
            self.redis_client = redis.Redis(
                host=config['host'],
                port=config['port'],
                db=config['db'],
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    def cache_latest_price(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Cache latest price for a symbol"""
        try:
            key = f"latest_price:{symbol}"
            value = json.dumps(data, default=str)
            self.redis_client.setex(
                key,
                db_config.CACHE_TTL_SECONDS,
                value
            )
            logger.info(f"✅ Cached {symbol} in Redis")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to cache price: {e}")
            return False
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """Get latest price from cache"""
        try:
            key = f"latest_price:{symbol}"
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get cached price: {e}")
            return None
    
    def cache_moving_average(self, symbol: str, data: Dict[str, Any]) -> bool:
        """Cache moving average"""
        try:
            key = f"moving_avg_5min:{symbol}"
            value = json.dumps(data, default=str)
            self.redis_client.setex(
                key,
                db_config.CACHE_TTL_SECONDS,
                value
            )
            logger.info(f"✅ Cached moving avg for {symbol}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to cache moving average: {e}")
            return False
    
    def get_all_latest_prices(self) -> Dict[str, Dict]:
        """Get all cached latest prices"""
        try:
            pattern = "latest_price:*"
            keys = self.redis_client.keys(pattern)
            result = {}
            for key in keys:
                symbol = key.split(':')[1]
                value = self.redis_client.get(key)
                if value:
                    result[symbol] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get all prices: {e}")
            return {}
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()
        logger.info("✅ Redis connection closed")


class StorageManager:
    """Combined storage manager"""
    
    def __init__(self):
        """Initialize storage manager"""
        self.postgres = PostgresStorage()
        self.redis = RedisCache()
        logger.info("Initializing StorageManager")
    
    def connect_all(self) -> bool:
        """Connect to all storage systems"""
        postgres_ok = self.postgres.connect()
        redis_ok = self.redis.connect()
        return postgres_ok and redis_ok
    
    def store_stock_data(self, data: Dict[str, Any]) -> bool:
        """Store stock data in both PostgreSQL and Redis"""
        # Store in PostgreSQL (permanent)
        postgres_ok = self.postgres.insert_stock_price(data)
        
        # Cache in Redis (hot data)
        redis_ok = self.redis.cache_latest_price(data['symbol'], data)
        
        return postgres_ok and redis_ok
    
    def store_moving_average(self, data: Dict[str, Any]) -> bool:
        """Store moving average in both systems"""
        postgres_ok = self.postgres.insert_moving_average(data)
        redis_ok = self.redis.cache_moving_average(data['symbol'], data)
        return postgres_ok and redis_ok
    
    def close_all(self):
        """Close all connections"""
        self.postgres.close()
        self.redis.close()
        logger.info("✅ All storage connections closed")


# Test function
def test_storage():
    """Test storage operations"""
    logger.info("╔════════════════════════════════════════════════╗")
    logger.info("║   TESTING STORAGE LAYER                        ║")
    logger.info("╚════════════════════════════════════════════════╝\n")
    
    storage = StorageManager()
    
    # Connect
    if not storage.connect_all():
        logger.error("Failed to connect to storage systems")
        return
    
    # Test data
    test_data = {
        'symbol': 'AAPL',
        'price': 275.50,
        'volume': 1000000,
        'market_cap': 3000000000000,
        'day_high': 276.00,
        'day_low': 274.00,
        'open': 274.50,
        'vwap': 275.25,
        'company_name': 'Apple Inc.',
        'source': 'Test',
        'timestamp': datetime.now().isoformat()
    }
    
    # Store
    logger.info("Testing storage...")
    if storage.store_stock_data(test_data):
        logger.info("✅ Test data stored successfully")
    
    # Retrieve from Redis
    cached = storage.redis.get_latest_price('AAPL')
    if cached:
        logger.info(f"✅ Retrieved from Redis: AAPL @ ${cached['price']}")
    
    # Retrieve from PostgreSQL
    history = storage.postgres.get_symbol_history('AAPL', hours=1)
    logger.info(f"✅ Retrieved {len(history)} records from PostgreSQL")
    
    # Cleanup
    storage.close_all()
    logger.info("\n✅ Storage test complete!")


if __name__ == '__main__':
    test_storage()
