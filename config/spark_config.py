"""
Spark Configuration
Handles Spark session and streaming configurations
"""

import os
from typing import Dict

class SparkConfig:
    """Spark configuration settings"""
    
    # Spark Application Settings
    APP_NAME = "RealTimeStockPipeline"
    MASTER = "local[*]"  # Use all available cores
    
    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'stock-prices')
    
    # Checkpoint location (for fault tolerance)
    CHECKPOINT_DIR = "./checkpoints/spark-streaming"
    
    # Streaming Settings
    TRIGGER_INTERVAL = "10 seconds"  # How often to process data
    
    # Window Settings
    WINDOW_DURATION_5MIN = "5 minutes"
    WINDOW_DURATION_15MIN = "15 minutes"
    WINDOW_DURATION_30MIN = "30 minutes"
    SLIDE_DURATION = "1 minute"  # How often windows update
    
    # Watermark (handle late data)
    WATERMARK_DURATION = "10 minutes"
    
    @classmethod
    def get_spark_conf(cls) -> Dict:
        """Get Spark configuration dictionary"""
        return {
            "spark.app.name": cls.APP_NAME,
            "spark.master": cls.MASTER,
            "spark.sql.streaming.checkpointLocation": cls.CHECKPOINT_DIR,
            "spark.sql.shuffle.partitions": "2",  # Reduce for local testing
            "spark.streaming.stopGracefullyOnShutdown": "true",
            "spark.sql.adaptive.enabled": "true",
        }
    
    @classmethod
    def get_kafka_options(cls) -> Dict:
        """Get Kafka connection options"""
        return {
            "kafka.bootstrap.servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "subscribe": cls.KAFKA_TOPIC,
            "startingOffsets": "latest",  # Start from latest messages
            "failOnDataLoss": "false",  # Don't fail if Kafka data is lost
        }

# Export configuration instance
spark_config = SparkConfig()
