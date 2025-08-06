-- Migration pour simplifier la table d'efficacité
-- Supprimer la colonne adjustment_ratio et calculer automatiquement

-- Supprimer l'ancienne colonne adjustment_ratio
ALTER TABLE machine_efficiency_curves DROP COLUMN IF EXISTS adjustment_ratio;

-- Fonction pour calculer le ratio d'ajustement automatiquement
CREATE OR REPLACE FUNCTION calculate_adjustment_ratio(
    p_machine_id INTEGER,
    p_power_consumption INTEGER
)
RETURNS DECIMAL(5,3) AS $$
DECLARE
    nominal_power INTEGER;
    ratio DECIMAL(5,3);
BEGIN
    -- Récupérer la puissance nominale de la machine
    SELECT power_nominal INTO nominal_power
    FROM mining_machines
    WHERE id = p_machine_id;
    
    -- Calculer le ratio
    ratio := p_power_consumption::DECIMAL / nominal_power::DECIMAL;
    
    -- Limiter entre 0.5 et 1.0
    IF ratio < 0.5 THEN
        ratio := 0.5;
    ELSIF ratio > 1.0 THEN
        ratio := 1.0;
    END IF;
    
    RETURN ratio;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour obtenir l'efficacité avec interpolation
CREATE OR REPLACE FUNCTION get_machine_efficiency_interpolated(
    p_machine_id INTEGER,
    p_adjustment_ratio DECIMAL(5,3)
)
RETURNS TABLE(
    effective_hashrate DECIMAL(15,2),
    power_consumption INTEGER
) AS $$
DECLARE
    lower_power INTEGER;
    upper_power INTEGER;
    lower_hashrate DECIMAL(15,2);
    upper_hashrate DECIMAL(15,2);
    interpolation_factor DECIMAL(5,3);
    target_power INTEGER;
    nominal_power INTEGER;
BEGIN
    -- Récupérer la puissance nominale
    SELECT power_nominal INTO nominal_power
    FROM mining_machines
    WHERE id = p_machine_id;
    
    -- Calculer la puissance cible
    target_power := (p_adjustment_ratio * nominal_power)::INTEGER;
    
    -- Trouver les points les plus proches
    SELECT power_consumption, effective_hashrate
    INTO lower_power, lower_hashrate
    FROM machine_efficiency_curves
    WHERE machine_id = p_machine_id AND power_consumption <= target_power
    ORDER BY power_consumption DESC
    LIMIT 1;
    
    SELECT power_consumption, effective_hashrate
    INTO upper_power, upper_hashrate
    FROM machine_efficiency_curves
    WHERE machine_id = p_machine_id AND power_consumption >= target_power
    ORDER BY power_consumption ASC
    LIMIT 1;
    
    -- Si on a trouvé des points, interpoler
    IF lower_power IS NOT NULL AND upper_power IS NOT NULL THEN
        IF lower_power = upper_power THEN
            -- Point exact trouvé
            RETURN QUERY SELECT lower_hashrate, lower_power;
        ELSE
            -- Interpolation linéaire
            interpolation_factor := (target_power - lower_power)::DECIMAL / (upper_power - lower_power)::DECIMAL;
            RETURN QUERY SELECT 
                lower_hashrate + (upper_hashrate - lower_hashrate) * interpolation_factor,
                target_power;
        END IF;
    ELSE
        -- Aucun point trouvé, retourner NULL
        RETURN QUERY SELECT NULL::DECIMAL(15,2), NULL::INTEGER;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Message de confirmation
SELECT 'Table d''efficacité simplifiée avec calcul automatique du ratio!' as status; 