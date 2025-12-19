"""
Database Configuration
PostgreSQL and Redis connection settings
"""

import os
from typing import Dict

class DatabaseConfig:
    """PostgreSQL configuration"""
    
    # PostgreSQL Settings
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'stockmarket')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'stockuser')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'stockpass')
    
    # JDBC URL for Spark
    JDBC_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Connection properties
    POSTGRES_PROPERTIES = {
        'user': POSTGRES_USER,
        'password': POSTGRES_PASSWORD,
        'driver': 'org.postgresql.Driver'
    }
    
    # Redis Settings
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Cache TTL
    CACHE_TTL_SECONDS = 300  # 5 minutes
    
    @classmethod
    def get_postgres_url(cls) -> str:
        """Get PostgreSQL connection URL for psycopg2"""
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    
    @classmethod
    def get_jdbc_url(cls) -> str:
        """Get JDBC URL for Spark"""
        return cls.JDBC_URL
    
    @classmethod
    def get_redis_config(cls) -> Dict:
        """Get Redis connection config"""
        return {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB
        }

# Export configuration instance
db_config = DatabaseConfig()
