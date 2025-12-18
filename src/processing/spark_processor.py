"""
Spark Stream Processor - Enhanced with Analytics
Processes stock data with moving averages and window aggregations
"""

import os
import sys

# Set JAVA_HOME before importing PySpark
os.environ['JAVA_HOME'] = '/opt/homebrew/opt/openjdk@17'
os.environ['PATH'] = f"/opt/homebrew/opt/openjdk@17/bin:{os.environ.get('PATH', '')}"

sys.path.append('.')

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, avg, max, min, count, sum,
    to_timestamp, current_timestamp, round as spark_round,
    expr, when
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    LongType, TimestampType
)

from src.utils.logger import setup_logger
from config.spark_config import spark_config

# Setup logger
logger = setup_logger(__name__, 'logs/spark_processor.log')


class StockStreamProcessor:
    """Process stock data streams with analytics"""
    
    def __init__(self):
        """Initialize Spark processor"""
        self.spark = None
        self.stream_query = None
        logger.info("Initializing Enhanced StockStreamProcessor")
    
    def create_spark_session(self):
        """Create and configure Spark session"""
        try:
            logger.info("Creating Spark session...")
            
            self.spark = SparkSession.builder \
                .appName(spark_config.APP_NAME) \
                .master(spark_config.MASTER) \
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
                .config("spark.sql.shuffle.partitions", "2") \
                .config("spark.driver.memory", "2g") \
                .config("spark.executor.memory", "2g") \
                .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("WARN")
            
            logger.info(f"✅ Spark session created: {spark_config.APP_NAME}")
            logger.info(f"✅ Spark version: {self.spark.version}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Spark session: {e}")
            return False
    
    def define_schema(self):
        """Define schema for incoming stock data"""
        return StructType([
            StructField("symbol", StringType(), False),
            StructField("price", DoubleType(), False),
            StructField("volume", LongType(), False),
            StructField("market_cap", LongType(), True),
            StructField("day_high", DoubleType(), True),
            StructField("day_low", DoubleType(), True),
            StructField("fifty_two_week_high", DoubleType(), True),
            StructField("fifty_two_week_low", DoubleType(), True),
            StructField("timestamp", StringType(), False),
            StructField("company_name", StringType(), True),
            StructField("open", DoubleType(), True),
            StructField("vwap", DoubleType(), True),
        ])
    
    def read_from_kafka(self):
        """Read streaming data from Kafka"""
        try:
            logger.info("Connecting to Kafka...")
            
            kafka_df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", spark_config.KAFKA_BOOTSTRAP_SERVERS) \
                .option("subscribe", spark_config.KAFKA_TOPIC) \
                .option("startingOffsets", "earliest") \
                .option("startingOffsets", "latest") \
                .option("failOnDataLoss", "false") \
                .load()
            
            logger.info("✅ Connected to Kafka stream")
            return kafka_df
            
        except Exception as e:
            logger.error(f"❌ Failed to read from Kafka: {e}")
            return None
    
    def parse_stock_data(self, kafka_df):
        """Parse JSON data from Kafka"""
        schema = self.define_schema()
        
        parsed_df = kafka_df \
            .select(
                from_json(col("value").cast("string"), schema).alias("data")
            ) \
            .select("data.*") \
            .withColumn("event_time", to_timestamp(col("timestamp")))
        
        logger.info("✅ Data parsing configured")
        return parsed_df
    
    def calculate_moving_averages(self, stock_df):
        """Calculate moving averages using window aggregations"""
        
        # 5-minute window aggregation
        windowed_5min = stock_df \
            .withWatermark("event_time", "10 minutes") \
            .groupBy(
                window(col("event_time"), "5 minutes", "1 minute"),
                col("symbol"),
                col("company_name")
            ) \
            .agg(
                spark_round(avg("price"), 2).alias("avg_price_5min"),
                spark_round(max("price"), 2).alias("max_price_5min"),
                spark_round(min("price"), 2).alias("min_price_5min"),
                sum("volume").alias("total_volume_5min"),
                count("*").alias("num_updates_5min")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("symbol"),
                col("company_name"),
                col("avg_price_5min"),
                col("max_price_5min"),
                col("min_price_5min"),
                col("total_volume_5min"),
                col("num_updates_5min")
            )
        
        logger.info("✅ 5-minute moving average configured")
        return windowed_5min
    
    def calculate_price_changes(self, stock_df):
        """
        Calculates price changes.
        NOTE: Standard 'lag' functions are disabled here as they cause
        streaming errors without stateful processing.
        """
        logger.info("ℹ️ Basic mode: Skipping stateful 'lag' calculations to prevent stream errors.")
        return stock_df
    
    def process_with_analytics(self):
        """Process stream with full analytics (Moving Averages)"""
        if not self.spark:
            if not self.create_spark_session():
                return
        
        # Read from Kafka
        kafka_df = self.read_from_kafka()
        if kafka_df is None:
            return
        
        # Parse data
        stock_df = self.parse_stock_data(kafka_df)
        
        # Calculate moving averages
        moving_avg_df = self.calculate_moving_averages(stock_df)
        
        logger.info("🚀 Starting analytics stream processing...")
        logger.info("📊 Calculating 5-minute moving averages")
        logger.info("Press Ctrl+C to stop\n")
        
        # Write moving averages to console
        query = moving_avg_df \
            .writeStream \
            .outputMode("update") \
            .format("console") \
            .option("truncate", "false") \
            .trigger(processingTime="5 seconds") \
            .start()
        
        self.stream_query = query
        
        try:
            query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping stream...")
            self.stop()
    
    def process_basic(self):
        """Basic processing"""
        if not self.spark:
            if not self.create_spark_session():
                return
        
        # Read and parse
        kafka_df = self.read_from_kafka()
        if kafka_df is None:
            return
        
        stock_df = self.parse_stock_data(kafka_df)
        
        # We skip the complex lag calculation to avoid the crash
        # with_analytics = self.calculate_price_changes(stock_df)
        
        logger.info("🚀 Starting basic stream processing...")
        logger.info("📈 Showing: symbol, price, volume, company")
        logger.info("Press Ctrl+C to stop\n")
        
        # Display with analytics
        query = stock_df \
            .select(
                "symbol",
                "price",
                "volume",
                "company_name",
                "event_time"
            ) \
            .writeStream \
            .outputMode("append") \
            .format("console") \
            .option("truncate", "false") \
            .trigger(processingTime="10 seconds") \
            .start()
        
        self.stream_query = query
        
        try:
            query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping stream...")
            self.stop()
    
    def stop(self):
        """Stop Spark session"""
        if self.stream_query:
            self.stream_query.stop()
            logger.info("✅ Stream query stopped")
        
        if self.spark:
            self.spark.stop()
            logger.info("✅ Spark session stopped")


def main():
    """Main function"""
    import sys
    
    logger.info("╔════════════════════════════════════════════════╗")
    logger.info("║   SPARK ANALYTICS PROCESSOR                    ║")
    logger.info("║   Real-Time Moving Averages & Indicators       ║")
    logger.info("╚════════════════════════════════════════════════╝\n")
    
    processor = StockStreamProcessor()
    
    # Check command line argument
    if len(sys.argv) > 1 and sys.argv[1] == "--analytics":
        logger.info("Mode: Analytics (5-minute moving averages)")
        processor.process_with_analytics()
    else:
        logger.info("Mode: Basic (Raw Stream)")
        logger.info("Use --analytics flag for moving averages")
        processor.process_basic()


if __name__ == '__main__':
    main()