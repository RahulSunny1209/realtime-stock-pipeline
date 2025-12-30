# src/config/spark_config.py

from pyspark.sql import SparkSession

def spark_config(app_name="StockPipeline"):
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
