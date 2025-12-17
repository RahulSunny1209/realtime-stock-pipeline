"""
Stock Data Consumer
Consumes stock data from Kafka for testing
"""

import json
import sys
sys.path.append('.')

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from src.utils.logger import setup_logger
from config.kafka_config import kafka_config
from typing import Optional

# Setup logger
logger = setup_logger(__name__, 'logs/consumer.log')

class StockConsumer:
    """Consumes stock data from Kafka"""
    
    def __init__(self):
        """Initialize consumer"""
        self.consumer: Optional[KafkaConsumer] = None
        self.topic = kafka_config.STOCK_TOPIC
        logger.info("Initializing StockConsumer")
    
    def connect(self):
        """Connect to Kafka"""
        try:
            consumer_config = kafka_config.get_consumer_config()
            
            # Add deserializers
            consumer_config['value_deserializer'] = lambda m: json.loads(m.decode('utf-8'))
            consumer_config['key_deserializer'] = lambda k: k.decode('utf-8') if k else None
            
            self.consumer = KafkaConsumer(
                self.topic,
                **consumer_config
            )
            
            logger.info(f"✅ Connected to Kafka, subscribed to '{self.topic}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def consume(self):
        """Start consuming messages"""
        if not self.consumer:
            if not self.connect():
                return
            
        if self.consumer is None:
            logger.error("❌ Consumer not initialized")
            return
        
        logger.info("🎧 Starting consumer...")
        logger.info("Waiting for messages (Press Ctrl+C to stop)\n")
        
        try:
            message_count = 0
            for message in self.consumer:
                message_count += 1
                
                # Extract data
                symbol = message.key
                data = message.value
                
                # Display message
                logger.info(f"\n{'='*60}")
                logger.info(f"Message #{message_count}")
                logger.info(f"{'='*60}")
                logger.info(f"Symbol: {symbol}")
                logger.info(f"Price: ${data['price']:.2f}")
                logger.info(f"Volume: {data['volume']:,}")
                logger.info(f"Company: {data['company_name']}")
                logger.info(f"Timestamp: {data['timestamp']}")
                logger.info(f"Partition: {message.partition}, Offset: {message.offset}")
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping consumer...")
            self.close()
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            self.close()
    
    def close(self):
        """Close consumer"""
        if self.consumer:
            self.consumer.close()
            logger.info("✅ Consumer closed")

def main():
    """Main function"""
    consumer = StockConsumer()
    consumer.consume()

if __name__ == '__main__':
    main()
