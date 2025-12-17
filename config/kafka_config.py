"""
Kafka Configuration
Handles Kafka connection settings and topic configurations
"""

import os
from typing import Dict

class KafkaConfig:
    """Kafka configuration settings"""
    
    # Kafka broker settings
    BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    # Topic settings
    STOCK_TOPIC = 'stock-prices'
    STOCK_TOPIC_PARTITIONS = 3
    STOCK_TOPIC_REPLICATION_FACTOR = 1
    
    # Producer settings
    PRODUCER_CONFIG: Dict = {
        'bootstrap_servers': BOOTSTRAP_SERVERS,
        'acks': 'all',  # Wait for all replicas to acknowledge
        'retries': 3,   # Retry failed sends
        'max_in_flight_requests_per_connection': 1,  # Ensure ordering
        'compression_type': 'gzip',  # Compress messages
        'linger_ms': 10,  # Batch messages for efficiency
    }
    
    # Consumer settings
    CONSUMER_CONFIG: Dict = {
        'bootstrap_servers': BOOTSTRAP_SERVERS,
        'group_id': 'stock-consumer-group',
        'auto_offset_reset': 'earliest',  # Start from beginning
        'enable_auto_commit': True,
        'auto_commit_interval_ms': 1000,
        'session_timeout_ms': 30000,
    }
    
    @classmethod
    def get_producer_config(cls) -> Dict:
        """Get producer configuration"""
        return cls.PRODUCER_CONFIG.copy()
    
    @classmethod
    def get_consumer_config(cls) -> Dict:
        """Get consumer configuration"""
        return cls.CONSUMER_CONFIG.copy()
    
    @classmethod
    def get_topic_config(cls) -> Dict:
        """Get topic configuration"""
        return {
            'name': cls.STOCK_TOPIC,
            'partitions': cls.STOCK_TOPIC_PARTITIONS,
            'replication_factor': cls.STOCK_TOPIC_REPLICATION_FACTOR,
        }

# Export configuration instance
kafka_config = KafkaConfig()
