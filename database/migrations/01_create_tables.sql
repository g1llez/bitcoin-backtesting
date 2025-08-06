-- Script d'initialisation de la base de données Bitcoin Backtesting
-- Ce script sera exécuté automatiquement au démarrage du container PostgreSQL

-- Table pour les prix historiques du Bitcoin
CREATE TABLE IF NOT EXISTS bitcoin_prices (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    price_usd DECIMAL(15,2) NOT NULL,
    price_cad DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour les données FPPS historiques
CREATE TABLE IF NOT EXISTS fpps_data (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    fpps_rate DECIMAL(20,8) NOT NULL,  -- Taux FPPS en BTC par TH/s
    network_difficulty BIGINT NOT NULL,  -- Difficulté du réseau
    network_hashrate DECIMAL(20,2) NOT NULL,  -- Hashrate réseau en TH/s
    block_reward DECIMAL(20,8) NOT NULL,  -- Récompense de bloc en BTC
    fees_total DECIMAL(20,8) NOT NULL,  -- Frais totaux en BTC
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour les machines Bitcoin
CREATE TABLE IF NOT EXISTS mining_machines (
    id SERIAL PRIMARY KEY,
    model VARCHAR(100) NOT NULL UNIQUE,
    manufacturer VARCHAR(100) NOT NULL,
    hashrate_nominal DECIMAL(15,2) NOT NULL,  -- TH/s
    power_nominal INTEGER NOT NULL,  -- Watts
    efficiency_base DECIMAL(10,2) NOT NULL,  -- J/TH
    price_usd DECIMAL(10,2),
    release_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour les résultats de backtesting
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES mining_machines(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    adjustment_ratio DECIMAL(5,3) NOT NULL,  -- Ratio d'ajustement (0.5 à 1.0)
    total_profit_usd DECIMAL(15,2) NOT NULL,
    total_cost_usd DECIMAL(15,2) NOT NULL,
    total_revenue_usd DECIMAL(15,2) NOT NULL,
    roi_percentage DECIMAL(8,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour les résultats quotidiens détaillés
CREATE TABLE IF NOT EXISTS daily_simulation (
    id SERIAL PRIMARY KEY,
    backtest_id INTEGER REFERENCES backtest_results(id),
    date DATE NOT NULL,
    machine_id INTEGER REFERENCES mining_machines(id),
    adjustment_ratio DECIMAL(5,3) NOT NULL,
    power_consumed_kwh DECIMAL(10,4) NOT NULL,
    revenue_usd DECIMAL(15,4) NOT NULL,
    cost_usd DECIMAL(15,4) NOT NULL,
    profit_usd DECIMAL(15,4) NOT NULL,
    roi_daily DECIMAL(8,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_bitcoin_prices_date ON bitcoin_prices(date);
CREATE INDEX IF NOT EXISTS idx_fpps_data_date ON fpps_data(date);
CREATE INDEX IF NOT EXISTS idx_backtest_results_dates ON backtest_results(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_daily_simulation_backtest_date ON daily_simulation(backtest_id, date);

-- Fonction pour mettre à jour le timestamp updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour mettre à jour updated_at automatiquement
CREATE TRIGGER update_bitcoin_prices_updated_at BEFORE UPDATE ON bitcoin_prices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fpps_data_updated_at BEFORE UPDATE ON fpps_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertion de données de test pour les machines
INSERT INTO mining_machines (model, manufacturer, hashrate_nominal, power_nominal, efficiency_base, price_usd, release_date) VALUES
('Antminer S19 Pro', 'Bitmain', 110.0, 3250, 29.5, 2000, '2020-05-01'),
('Antminer S21', 'Bitmain', 200.0, 3010, 15.05, 3500, '2023-06-01'),
('Antminer S19 XP', 'Bitmain', 140.0, 3010, 21.5, 2500, '2022-01-01')
ON CONFLICT (model) DO NOTHING;

-- Message de confirmation
SELECT 'Base de données Bitcoin Backtesting initialisée avec succès!' as status; 