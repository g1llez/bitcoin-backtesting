-- Ajout d'une table de cache pour les données de marché

CREATE TABLE IF NOT EXISTS market_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(50) UNIQUE NOT NULL,
    cache_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_market_cache_key ON market_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_market_cache_updated ON market_cache(updated_at);

-- Insérer les clés de cache initiales
INSERT INTO market_cache (cache_key, cache_value) VALUES 
    ('bitcoin_price', '{"price": null, "currency": "CAD"}'),
    ('fpps_rate', '{"rate": null, "unit": "BTC/day/TH/s"}')
ON CONFLICT (cache_key) DO NOTHING;

-- Fonction pour mettre à jour le cache
CREATE OR REPLACE FUNCTION update_market_cache(
    p_cache_key VARCHAR(50),
    p_cache_value JSONB
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO market_cache (cache_key, cache_value, updated_at)
    VALUES (p_cache_key, p_cache_value, NOW())
    ON CONFLICT (cache_key) 
    DO UPDATE SET 
        cache_value = p_cache_value,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Fonction pour récupérer le cache avec vérification de fraîcheur
CREATE OR REPLACE FUNCTION get_market_cache(
    p_cache_key VARCHAR(50),
    p_max_age_minutes INTEGER DEFAULT 1
)
RETURNS JSONB AS $$
DECLARE
    v_cache_record market_cache%ROWTYPE;
BEGIN
    SELECT * INTO v_cache_record
    FROM market_cache
    WHERE cache_key = p_cache_key
    AND updated_at > NOW() - INTERVAL '1 minute' * p_max_age_minutes;
    
    IF v_cache_record IS NOT NULL THEN
        RETURN v_cache_record.cache_value;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Message de confirmation
SELECT 'Table de cache des données de marché créée avec succès!' as status; 