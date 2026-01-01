# System Architecture

## Data Flow Diagram
```mermaid
graph LR
    A[Finnhub API] -->|REST API<br/>30s interval| B[Producer]
    B -->|JSON messages| C[Kafka<br/>3 partitions]
    C -->|Stream| D[Spark<br/>Streaming]
    D -->|Batch write<br/>30s| E[PostgreSQL]
    D -->|Cache<br/>5min TTL| F[Redis]
    E -->|Query| G[Dashboard]
    F -->|Hot data| G
    G -->|Display| H[User Browser]
    
    style A fill:#e1f5ff
    style B fill:#fff3cd
    style C fill:#d4edda
    style D fill:#f8d7da
    style E fill:#d1ecf1
    style F fill:#d1ecf1
    style G fill:#e2e3e5
    style H fill:#f8f9fa
```

## Container Architecture
```mermaid
graph TB
    subgraph "Docker Network: stock-pipeline-network"
        subgraph "Infrastructure Layer"
            ZK[Zookeeper<br/>:2181]
            K[Kafka<br/>:9092]
            P[PostgreSQL<br/>:5432]
            R[Redis<br/>:6379]
        end
        
        subgraph "Application Layer"
            PROD[Producer<br/>Container]
            SPARK[Spark Processor<br/>Container]
            DASH[Dashboard<br/>Container<br/>:8501]
        end
        
        subgraph "Monitoring Layer"
            KUI[Kafka UI<br/>:8080]
            PGA[pgAdmin<br/>:5050]
        end
    end
    
    PROD --> K
    K --> SPARK
    SPARK --> P
    SPARK --> R
    P --> DASH
    R --> DASH
    ZK --> K
    K --> KUI
    P --> PGA
    
    style ZK fill:#ffc107
    style K fill:#28a745
    style P fill:#007bff
    style R fill:#dc3545
    style PROD fill:#6f42c1
    style SPARK fill:#e83e8c
    style DASH fill:#20c997
    style KUI fill:#6c757d
    style PGA fill:#17a2b8
```

## Technology Stack
```mermaid
graph TD
    A[Real-Time Stock Pipeline] --> B[Data Ingestion]
    A --> C[Stream Processing]
    A --> D[Data Storage]
    A --> E[Visualization]
    A --> F[Infrastructure]
    
    B --> B1[Python 3.11]
    B --> B2[Finnhub API]
    B --> B3[kafka-python]
    
    C --> C1[Apache Spark 3.5.0]
    C --> C2[PySpark]
    C --> C3[Structured Streaming]
    
    D --> D1[PostgreSQL 16]
    D --> D2[Redis 7]
    D --> D3[psycopg2]
    
    E --> E1[Streamlit 1.29.0]
    E --> E2[Plotly 5.18.0]
    E --> E3[Pandas 2.1.4]
    
    F --> F1[Docker]
    F --> F2[Docker Compose]
    F --> F3[Kafka 7.5.0]
```

## Database Schema
```sql
-- Stock Prices (Time-Series Data)
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    volume BIGINT,
    day_high DECIMAL(10, 2),
    day_low DECIMAL(10, 2),
    open_price DECIMAL(10, 2),
    event_time TIMESTAMP NOT NULL,
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, event_time)
);

-- Indexes for fast queries
CREATE INDEX idx_symbol_time ON stock_prices(symbol, event_time DESC);
CREATE INDEX idx_event_time ON stock_prices(event_time DESC);
```

## Deployment Flow
```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as Git Repository
    participant Docker as Docker Build
    participant Compose as Docker Compose
    participant AWS as AWS EC2
    
    Dev->>Git: git push
    Git->>Docker: Trigger build
    Docker->>Docker: Build 3 images<br/>(producer, spark, dashboard)
    Docker->>Compose: Push images
    Compose->>AWS: Deploy containers
    AWS->>AWS: Start 9 services
    AWS-->>Dev: Live URL ready
```
