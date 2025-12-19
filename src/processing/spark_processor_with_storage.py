"""
Spark Stream Processor with Database Storage
Automatically saves processed data to PostgreSQL and Redis
"""

import os
import sys

# Set JAVA_HOME
os.environ['JAVA_HOME'] = '/opt/homebrew/opt/openjdk@17'
os.environ['PATH'] = f"/opt/homebrew/opt/openjdk@17/bin:{os.environ['PATH']}"

sys.path.append('.')

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, window, avg, max, min, count, sum,
    to_timestamp, current_timestamp, round as spark_round
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    LongType, TimestampType
)

from src.utils.logger import setup_logger
from config.spark_config import spark_config
from config.db_config import db_config

# Setup logger
logger = setup_logger(__name__, 'logs/spark_storage.log')


class SparkToPostgres:
    """Spark Structured Streaming to PostgreSQL"""
    
    def __init__(self):
        """Initialize processor"""
        self.spark = None
        self.stream_query = None
        logger.info("Initializing Spark → PostgreSQL Processor")
    
    def create_spark_session(self):
        """Create Spark session with PostgreSQL JDBC driver"""
        try:
            logger.info("Creating Spark session with PostgreSQL support...")
            
            self.spark = SparkSession.builder \
                .appName("StockPipeline-Storage") \
                .master(spark_config.MASTER) \
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                       "org.postgresql:postgresql:42.7.1") \
                .config("spark.sql.shuffle.partitions", "2") \
                .config("spark.driver.memory", "2g") \
                .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("WARN")
            
            logger.info(f"✅ Spark session created with PostgreSQL JDBC")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create Spark session: {e}")
            return False
    
    def define_schema(self):
        """Define schema for stock data"""
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
        """Read from Kafka"""
        try:
            logger.info("Connecting to Kafka...")
            
            kafka_df = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", spark_config.KAFKA_BOOTSTRAP_SERVERS) \
                .option("subscribe", spark_config.KAFKA_TOPIC) \
                .option("startingOffsets", "latest") \
                .option("failOnDataLoss", "false") \
                .load()
            
            logger.info("✅ Connected to Kafka")
            return kafka_df
            
        except Exception as e:
            logger.error(f"❌ Failed to read from Kafka: {e}")
            return None
    
    def parse_stock_data(self, kafka_df):
        """Parse JSON from Kafka"""
        schema = self.define_schema()
        
        parsed_df = kafka_df \
            .select(
                from_json(col("value").cast("string"), schema).alias("data")
            ) \
            .select("data.*") \
            .withColumn("event_time", to_timestamp(col("timestamp")))
        
        # Select and rename columns for PostgreSQL
        final_df = parsed_df.select(
            col("symbol"),
            col("price"),
            col("volume"),
            col("market_cap"),
            col("day_high"),
            col("day_low"),
            col("open").alias("open_price"),
            col("vwap"),
            col("company_name"),
            col("event_time")
        )
        
        logger.info("✅ Data parsing configured")
        return final_df
    
    def write_to_postgres_batch(self, batch_df, batch_id):
        """
        Write each micro-batch to PostgreSQL
        This is called for each streaming batch
        """
        try:
            if batch_df.count() == 0:
                return
            
            logger.info(f"📦 Writing batch {batch_id} with {batch_df.count()} records")
            
            # JDBC write to PostgreSQL
            batch_df.write \
                .format("jdbc") \
                .option("url", db_config.JDBC_URL) \
                .option("dbtable", "stock_prices") \
                .option("user", db_config.POSTGRES_USER) \
                .option("password", db_config.POSTGRES_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            logger.info(f"✅ Batch {batch_id} written to PostgreSQL")
            
        except Exception as e:
            logger.error(f"❌ Error writing batch {batch_id}: {e}")
    
    def process_and_store(self):
        """Process stream and store in PostgreSQL"""
        if not self.spark:
            if not self.create_spark_session():
                return
        
        # Read from Kafka
        kafka_df = self.read_from_kafka()
        if kafka_df is None:
            return
        
        # Parse data
        stock_df = self.parse_stock_data(kafka_df)
        
        logger.info("🚀 Starting Spark → PostgreSQL streaming...")
        logger.info("📊 Data will be saved to PostgreSQL automatically")
        logger.info("Press Ctrl+C to stop\n")
        
        # Write stream using foreachBatch
        query = stock_df \
            .writeStream \
            .foreachBatch(self.write_to_postgres_batch) \
            .outputMode("append") \
            .trigger(processingTime="30 seconds") \
            .option("checkpointLocation", "./checkpoints/postgres-sink") \
            .start()
        
        self.stream_query = query
        
        try:
            query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping stream...")
            self.stop()
    
    def process_with_console_and_storage(self):
        """Show in console AND save to PostgreSQL"""
        if not self.spark:
            if not self.create_spark_session():
                return
        
        kafka_df = self.read_from_kafka()
        if kafka_df is None:
            return
        
        stock_df = self.parse_stock_data(kafka_df)
        
        logger.info("🚀 Dual mode: Console + PostgreSQL")
        logger.info("Press Ctrl+C to stop\n")
        
        # Console output
        console_query = stock_df \
            .select("symbol", "price", "volume", "company_name", "event_time") \
            .writeStream \
            .outputMode("append") \
            .format("console") \
            .option("truncate", "false") \
            .trigger(processingTime="10 seconds") \
            .start()
        
        # PostgreSQL storage
        storage_query = stock_df \
            .writeStream \
            .foreachBatch(self.write_to_postgres_batch) \
            .outputMode("append") \
            .trigger(processingTime="30 seconds") \
            .option("checkpointLocation", "./checkpoints/postgres-dual") \
            .start()
        
        try:
            storage_query.awaitTermination()
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping streams...")
            console_query.stop()
            storage_query.stop()
            self.stop()
    
    def stop(self):
        """Stop Spark"""
        if self.spark:
            self.spark.stop()
            logger.info("✅ Spark stopped")


def main():
    """Main function"""
    logger.info("╔════════════════════════════════════════════════╗")
    logger.info("║   SPARK → POSTGRESQL STORAGE PIPELINE         ║")
    logger.info("║   Automatic Data Persistence                   ║")
    logger.info("╚════════════════════════════════════════════════╝\n")
    
    processor = SparkToPostgres()
    
    # Check command line
    if len(sys.argv) > 1 and sys.argv[1] == "--dual":
        logger.info("Mode: Dual (Console + Storage)")
        processor.process_with_console_and_storage()
    else:
        logger.info("Mode: Storage Only")
        logger.info("Use --dual flag for console output")
        processor.process_and_store()


if __name__ == '__main__':
    main()
