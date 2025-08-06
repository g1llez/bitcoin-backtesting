-- Table pour modéliser l'efficacité variable des machines selon le ratio d'ajustement
-- Basée sur des données de tests réels
CREATE TABLE IF NOT EXISTS machine_efficiency_curves (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES mining_machines(id),
    adjustment_ratio DECIMAL(5,3) NOT NULL,  -- Ratio d'ajustement (0.5 à 1.0)
    effective_hashrate DECIMAL(15,2) NOT NULL,  -- TH/s effectif (mesuré)
    power_consumption INTEGER NOT NULL,  -- Watts consommés (mesuré)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(machine_id, adjustment_ratio)
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_machine_efficiency_machine_ratio ON machine_efficiency_curves(machine_id, adjustment_ratio);

-- Fonction pour obtenir l'efficacité d'une machine selon le ratio
CREATE OR REPLACE FUNCTION get_machine_efficiency(
    p_machine_id INTEGER,
    p_adjustment_ratio DECIMAL(5,3)
)
RETURNS TABLE(
    effective_hashrate DECIMAL(15,2),
    power_consumption INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mec.effective_hashrate,
        mec.power_consumption
    FROM machine_efficiency_curves mec
    WHERE mec.machine_id = p_machine_id 
    AND mec.adjustment_ratio = p_adjustment_ratio;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour interpoler entre deux points si le ratio exact n'existe pas
CREATE OR REPLACE FUNCTION get_machine_efficiency_interpolated(
    p_machine_id INTEGER,
    p_adjustment_ratio DECIMAL(5,3)
)
RETURNS TABLE(
    effective_hashrate DECIMAL(15,2),
    power_consumption INTEGER
) AS $$
DECLARE
    lower_ratio DECIMAL(5,3);
    upper_ratio DECIMAL(5,3);
    lower_hashrate DECIMAL(15,2);
    upper_hashrate DECIMAL(15,2);
    lower_power INTEGER;
    upper_power INTEGER;
    interpolation_factor DECIMAL(5,3);
BEGIN
    -- Trouver les points les plus proches
    SELECT adjustment_ratio, effective_hashrate, power_consumption
    INTO lower_ratio, lower_hashrate, lower_power
    FROM machine_efficiency_curves
    WHERE machine_id = p_machine_id AND adjustment_ratio <= p_adjustment_ratio
    ORDER BY adjustment_ratio DESC
    LIMIT 1;
    
    SELECT adjustment_ratio, effective_hashrate, power_consumption
    INTO upper_ratio, upper_hashrate, upper_power
    FROM machine_efficiency_curves
    WHERE machine_id = p_machine_id AND adjustment_ratio >= p_adjustment_ratio
    ORDER BY adjustment_ratio ASC
    LIMIT 1;
    
    -- Si on a trouvé des points, interpoler
    IF lower_ratio IS NOT NULL AND upper_ratio IS NOT NULL THEN
        IF lower_ratio = upper_ratio THEN
            -- Point exact trouvé
            RETURN QUERY SELECT lower_hashrate, lower_power;
        ELSE
            -- Interpolation linéaire
            interpolation_factor := (p_adjustment_ratio - lower_ratio) / (upper_ratio - lower_ratio);
            RETURN QUERY SELECT 
                lower_hashrate + (upper_hashrate - lower_hashrate) * interpolation_factor,
                lower_power + (upper_power - lower_power) * interpolation_factor;
        END IF;
    ELSE
        -- Aucun point trouvé, retourner NULL
        RETURN QUERY SELECT NULL::DECIMAL(15,2), NULL::INTEGER;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Message de confirmation
SELECT 'Table d''efficacité des machines créée avec succès! (Données réelles à insérer)' as status; 