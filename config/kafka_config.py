"""
Kafka Configuration
"""

import os
from typing import Dict

class KafkaConfig:
    """Kafka configuration settings"""
    
    BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    STOCK_TOPIC = 'stock-prices'
    STOCK_TOPIC_PARTITIONS = 3
    STOCK_TOPIC_REPLICATION_FACTOR = 1
    
    PRODUCER_CONFIG: Dict = {
        'bootstrap_servers': BOOTSTRAP_SERVERS,
        'acks': 'all',
        'retries': 3,
        'max_in_flight_requests_per_connection': 1,
        'compression_type': 'gzip',
        'linger_ms': 10,
    }
    
    CONSUMER_CONFIG: Dict = {
        'bootstrap_servers': BOOTSTRAP_SERVERS,
        'group_id': 'stock-consumer-group',
        'auto_offset_reset': 'earliest',
        'enable_auto_commit': True,
        'auto_commit_interval_ms': 1000,
        'session_timeout_ms': 30000,
    }
    
    @classmethod
    def get_producer_config(cls) -> Dict:
        return cls.PRODUCER_CONFIG.copy()
    
    @classmethod
    def get_consumer_config(cls) -> Dict:
        return cls.CONSUMER_CONFIG.copy()
    
    @classmethod
    def get_topic_config(cls) -> Dict:
        return {
            'name': cls.STOCK_TOPIC,
            'partitions': cls.STOCK_TOPIC_PARTITIONS,
            'replication_factor': cls.STOCK_TOPIC_REPLICATION_FACTOR,
        }

kafka_config = KafkaConfig()
