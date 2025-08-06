-- Migration pour restructurer le système de machines en templates et instances
-- Les machines existantes deviennent des templates

-- Renommer la table pour clarifier qu'il s'agit de templates
ALTER TABLE mining_machines RENAME TO machine_templates;

-- Ajouter une colonne pour identifier les templates actifs
ALTER TABLE machine_templates ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- Créer une nouvelle table pour les instances de machines dans les sites
CREATE TABLE site_machine_instances (
    id SERIAL PRIMARY KEY,
    site_id INTEGER REFERENCES mining_sites(id) ON DELETE CASCADE,
    template_id INTEGER REFERENCES machine_templates(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    custom_name VARCHAR(100), -- Nom personnalisé pour cette instance
    notes TEXT, -- Notes spécifiques à cette instance
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Supprimer l'ancienne table site_machines qui n'est plus nécessaire
DROP TABLE IF EXISTS site_machines;

-- Fonction pour calculer le hashrate total d'un site
CREATE OR REPLACE FUNCTION calculate_site_total_hashrate(p_site_id INTEGER)
RETURNS DECIMAL(15,2) AS $$
DECLARE
    total_hashrate DECIMAL(15,2) := 0;
BEGIN
    SELECT COALESCE(SUM(mt.hashrate_nominal * smi.quantity), 0)
    INTO total_hashrate
    FROM site_machine_instances smi
    JOIN machine_templates mt ON smi.template_id = mt.id
    WHERE smi.site_id = p_site_id;
    
    RETURN total_hashrate;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer la puissance totale d'un site
CREATE OR REPLACE FUNCTION calculate_site_total_power(p_site_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    total_power INTEGER := 0;
BEGIN
    SELECT COALESCE(SUM(mt.power_nominal * smi.quantity), 0)
    INTO total_power
    FROM site_machine_instances smi
    JOIN machine_templates mt ON smi.template_id = mt.id
    WHERE smi.site_id = p_site_id;
    
    RETURN total_power;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer le profit quotidien d'un site
CREATE OR REPLACE FUNCTION calculate_site_daily_profit(
    p_site_id INTEGER,
    p_bitcoin_price DECIMAL(10,2),
    p_fpps_sats INTEGER
)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    site_hashrate DECIMAL(15,2);
    site_power INTEGER;
    daily_profit DECIMAL(10,2);
BEGIN
    -- Récupérer le hashrate et la puissance total du site
    site_hashrate := calculate_site_total_hashrate(p_site_id);
    site_power := calculate_site_total_power(p_site_id);
    
    -- Calculer le profit avec la fonction existante
    daily_profit := calculate_daily_profit_tiered(
        p_site_id,
        site_hashrate,
        site_power,
        p_bitcoin_price,
        p_fpps_sats
    );
    
    RETURN daily_profit;
END;
$$ LANGUAGE plpgsql;

-- Vue pour faciliter l'affichage des sites avec leurs machines
CREATE VIEW site_machines_view AS
SELECT 
    s.id as site_id,
    s.name as site_name,
    s.address as site_address,
    smi.id as instance_id,
    smi.quantity,
    smi.custom_name,
    smi.notes,
    mt.id as template_id,
    mt.model as machine_model,
    mt.manufacturer,
    mt.hashrate_nominal,
    mt.power_nominal,
    mt.efficiency_base,
    (mt.hashrate_nominal * smi.quantity) as total_hashrate,
    (mt.power_nominal * smi.quantity) as total_power
FROM mining_sites s
LEFT JOIN site_machine_instances smi ON s.id = smi.site_id
LEFT JOIN machine_templates mt ON smi.template_id = mt.id
WHERE s.id IS NOT NULL;

-- Message de confirmation
SELECT 'Système de templates de machines créé avec succès!' as status; 