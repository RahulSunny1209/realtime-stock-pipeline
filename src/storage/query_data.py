"""
Query Interface for Stock Data
Easy access to stored data
"""

import sys
sys.path.append('.')

from src.storage.database import StorageManager
from src.utils.logger import setup_logger
from tabulate import tabulate

logger = setup_logger(__name__, 'logs/query.log')


def main():
    """Query and display stock data"""
    storage = StorageManager()
    
    if not storage.connect_all():
        logger.error("Failed to connect to storage")
        return
    
    print("\n" + "="*60)
    print("STOCK DATA QUERY INTERFACE")
    print("="*60 + "\n")
    
    # Latest prices
    print("📊 LATEST PRICES:")
    print("-" * 60)
    latest = storage.postgres.get_latest_prices(limit=10)
    if latest:
        print(tabulate(
            [[r['symbol'], f"${r['price']:.2f}", r['volume'], r['event_time']] 
             for r in latest],
            headers=['Symbol', 'Price', 'Volume', 'Time'],
            tablefmt='grid'
        ))
    
    # Redis cache
    print("\n🔴 REDIS CACHE:")
    print("-" * 60)
    cached = storage.redis.get_all_latest_prices()
    if cached:
        print(f"Cached symbols: {', '.join(cached.keys())}")
        for symbol, data in cached.items():
            print(f"  {symbol}: ${data['price']}")
    
    # Symbol history
    print("\n📈 AAPL HISTORY (last 24 hours):")
    print("-" * 60)
    history = storage.postgres.get_symbol_history('AAPL', hours=24)
    if history:
        print(f"Total records: {len(history)}")
        if len(history) > 0:
            print(tabulate(
                [[h['symbol'], f"${h['price']:.2f}", h['volume'], h['event_time']] 
                 for h in history[:5]],
                headers=['Symbol', 'Price', 'Volume', 'Time'],
                tablefmt='grid'
            ))
    
    storage.close_all()
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
