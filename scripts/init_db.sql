-- Real-Time Stock Market Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Raw Stock Prices Table
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    volume BIGINT DEFAULT 0,
    market_cap BIGINT,
    day_high DECIMAL(10, 2),
    day_low DECIMAL(10, 2),
    open_price DECIMAL(10, 2),
    vwap DECIMAL(10, 2),
    company_name VARCHAR(255),
    source VARCHAR(50) DEFAULT 'Finnhub',
    event_time TIMESTAMP NOT NULL,
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_symbol_time UNIQUE (symbol, event_time)
);

CREATE INDEX idx_stock_prices_symbol_time ON stock_prices (symbol, event_time DESC);
CREATE INDEX idx_stock_prices_event_time ON stock_prices (event_time DESC);
CREATE INDEX idx_stock_prices_symbol ON stock_prices (symbol);

-- Moving Averages Table
CREATE TABLE IF NOT EXISTS stock_moving_averages (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    avg_price_5min DECIMAL(10, 2),
    max_price_5min DECIMAL(10, 2),
    min_price_5min DECIMAL(10, 2),
    total_volume_5min BIGINT,
    num_updates INT,
    calculation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_symbol_window UNIQUE (symbol, window_start, window_end)
);

CREATE INDEX idx_moving_avg_symbol_window ON stock_moving_averages (symbol, window_start DESC);
CREATE INDEX idx_moving_avg_window_start ON stock_moving_averages (window_start DESC);

-- Stock Metadata Table
CREATE TABLE IF NOT EXISTS stock_metadata (
    symbol VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    fifty_two_week_high DECIMAL(10, 2),
    fifty_two_week_low DECIMAL(10, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Views
CREATE OR REPLACE VIEW latest_stock_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    price,
    volume,
    day_high,
    day_low,
    event_time,
    company_name
FROM stock_prices
ORDER BY symbol, event_time DESC;

CREATE OR REPLACE VIEW hourly_stock_stats AS
SELECT
    symbol,
    DATE_TRUNC('hour', event_time) AS hour,
    AVG(price)::DECIMAL(10,2) AS avg_price,
    MAX(price) AS max_price,
    MIN(price) AS min_price,
    SUM(volume) AS total_volume,
    COUNT(*) AS num_updates
FROM stock_prices
GROUP BY symbol, DATE_TRUNC('hour', event_time)
ORDER BY hour DESC, symbol;

-- Seed Data
INSERT INTO stock_metadata (symbol, company_name, sector, industry) VALUES
    ('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics'),
    ('GOOGL', 'Alphabet Inc. Class A', 'Technology', 'Internet Content & Information'),
    ('MSFT', 'Microsoft Corporation', 'Technology', 'Software—Infrastructure'),
    ('AMZN', 'Amazon.com Inc', 'Consumer Cyclical', 'Internet Retail'),
    ('TSLA', 'Tesla, Inc.', 'Consumer Cyclical', 'Auto Manufacturers')
ON CONFLICT (symbol) DO NOTHING;

-- Permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO stockuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO stockuser;
