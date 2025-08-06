-- Migration pour ajouter la configuration et les sites
-- Création des nouvelles tables

-- Table de configuration
CREATE TABLE app_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table des sites de minage
CREATE TABLE mining_sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    electricity_tier1_rate DECIMAL(5,4) DEFAULT 0.0730, -- Prix pour premier 40kWh (Québec)
    electricity_tier2_rate DECIMAL(5,4) DEFAULT 0.0890, -- Prix après 40kWh (Québec)
    electricity_tier1_limit INTEGER DEFAULT 40, -- Limite en kWh
    braiins_token VARCHAR(255), -- Token pour l'API Braiins
    preferred_currency VARCHAR(3) DEFAULT 'CAD',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table de liaison sites-machines
CREATE TABLE site_machines (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES mining_sites(id) ON DELETE CASCADE,
    machine_id INTEGER REFERENCES mining_machines(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(site_id, machine_id)
);

-- Configuration par défaut
INSERT INTO app_config (key, value, description) VALUES
('default_theme', 'dark', 'Thème par défaut de l''interface'),
('braiins_api_url', 'https://pool.braiins.com/stats/json/btc', 'URL de l''API Braiins Pool'),
('coingecko_api_url', 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,cad', 'URL de l''API CoinGecko');

-- Site par défaut
INSERT INTO mining_sites (name, address, electricity_tier1_rate, electricity_tier2_rate) VALUES
('Site Principal', 'Adresse par défaut', 0.0730, 0.0890);

-- Fonction pour calculer le coût d'électricité avec paliers
CREATE OR REPLACE FUNCTION calculate_electricity_cost_tiered(
    p_site_id INTEGER,
    p_daily_kwh DECIMAL(10,2)
)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    site_record RECORD;
    tier1_cost DECIMAL(10,2);
    tier2_cost DECIMAL(10,2);
    tier2_kwh DECIMAL(10,2);
BEGIN
    -- Récupérer les informations du site
    SELECT electricity_tier1_rate, electricity_tier2_rate, electricity_tier1_limit
    INTO site_record
    FROM mining_sites
    WHERE id = p_site_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Site non trouvé';
    END IF;
    
    -- Calculer le coût avec paliers
    IF p_daily_kwh <= site_record.electricity_tier1_limit THEN
        -- Tout dans le premier palier
        RETURN p_daily_kwh * site_record.electricity_tier1_rate;
    ELSE
        -- Répartition entre paliers
        tier1_cost := site_record.electricity_tier1_limit * site_record.electricity_tier1_rate;
        tier2_kwh := p_daily_kwh - site_record.electricity_tier1_limit;
        tier2_cost := tier2_kwh * site_record.electricity_tier2_rate;
        
        RETURN tier1_cost + tier2_cost;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer le profit avec paliers d'électricité
CREATE OR REPLACE FUNCTION calculate_daily_profit_tiered(
    p_site_id INTEGER,
    p_hashrate DECIMAL(15,2),
    p_power_consumption INTEGER,
    p_bitcoin_price DECIMAL(10,2),
    p_fpps_sats INTEGER
)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    daily_revenue DECIMAL(10,2);
    daily_electricity_cost DECIMAL(10,2);
    daily_profit DECIMAL(10,2);
    fpps_btc DECIMAL(20,8);
BEGIN
    -- Calculer le revenu basé sur le hashrate et FPPS
    fpps_btc := p_fpps_sats::DECIMAL / 100000000;
    daily_revenue := p_hashrate * fpps_btc * p_bitcoin_price;
    
    -- Calculer le coût d'électricité avec paliers
    daily_electricity_cost := calculate_electricity_cost_tiered(
        p_site_id, 
        (p_power_consumption * 24)::DECIMAL / 1000
    );
    
    -- Calculer le profit
    daily_profit := daily_revenue - daily_electricity_cost;
    
    RETURN daily_profit;
END;
$$ LANGUAGE plpgsql;

-- Message de confirmation
SELECT 'Tables de configuration et sites créées avec succès!' as status; 