"""
Spark Configuration
"""

import os
from typing import Dict

class SparkConfig:
    """Spark configuration settings"""
    
    APP_NAME = "RealTimeStockPipeline"
    MASTER = "local[*]"
    
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'stock-prices')
    
    CHECKPOINT_DIR = "./checkpoints/spark-streaming"
    
    TRIGGER_INTERVAL = "10 seconds"
    
    WINDOW_DURATION_5MIN = "5 minutes"
    WINDOW_DURATION_15MIN = "15 minutes"
    WINDOW_DURATION_30MIN = "30 minutes"
    SLIDE_DURATION = "1 minute"
    
    WATERMARK_DURATION = "10 minutes"
    
    @classmethod
    def get_spark_conf(cls) -> Dict:
        return {
            "spark.app.name": cls.APP_NAME,
            "spark.master": cls.MASTER,
            "spark.sql.streaming.checkpointLocation": cls.CHECKPOINT_DIR,
            "spark.sql.shuffle.partitions": "2",
            "spark.streaming.stopGracefullyOnShutdown": "true",
            "spark.sql.adaptive.enabled": "true",
        }
    
    @classmethod
    def get_kafka_options(cls) -> Dict:
        return {
            "kafka.bootstrap.servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "subscribe": cls.KAFKA_TOPIC,
            "startingOffsets": "latest",
            "failOnDataLoss": "false",
        }

spark_config = SparkConfig()
