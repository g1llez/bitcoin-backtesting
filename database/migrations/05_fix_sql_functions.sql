-- Correction des fonctions SQL pour éviter les conflits de noms

-- Recréer la fonction d'interpolation avec des noms de variables non ambigus
CREATE OR REPLACE FUNCTION get_machine_efficiency_interpolated(
    p_machine_id INTEGER,
    p_adjustment_ratio DECIMAL(5,3)
)
RETURNS TABLE(
    effective_hashrate DECIMAL(15,2),
    power_consumption INTEGER
) AS $$
DECLARE
    v_lower_power INTEGER;
    v_upper_power INTEGER;
    v_lower_hashrate DECIMAL(15,2);
    v_upper_hashrate DECIMAL(15,2);
    v_interpolation_factor DECIMAL(5,3);
    v_target_power INTEGER;
    v_nominal_power INTEGER;
BEGIN
    -- Récupérer la puissance nominale
    SELECT power_nominal INTO v_nominal_power
    FROM mining_machines
    WHERE id = p_machine_id;
    
    -- Calculer la puissance cible
    v_target_power := (p_adjustment_ratio * v_nominal_power)::INTEGER;
    
    -- Trouver les points les plus proches
    SELECT mec.power_consumption, mec.effective_hashrate
    INTO v_lower_power, v_lower_hashrate
    FROM machine_efficiency_curves mec
    WHERE mec.machine_id = p_machine_id AND mec.power_consumption <= v_target_power
    ORDER BY mec.power_consumption DESC
    LIMIT 1;
    
    SELECT mec.power_consumption, mec.effective_hashrate
    INTO v_upper_power, v_upper_hashrate
    FROM machine_efficiency_curves mec
    WHERE mec.machine_id = p_machine_id AND mec.power_consumption >= v_target_power
    ORDER BY mec.power_consumption ASC
    LIMIT 1;
    
    -- Si on a trouvé des points, interpoler
    IF v_lower_power IS NOT NULL AND v_upper_power IS NOT NULL THEN
        IF v_lower_power = v_upper_power THEN
            -- Point exact trouvé
            RETURN QUERY SELECT v_lower_hashrate, v_lower_power;
        ELSE
            -- Interpolation linéaire
            v_interpolation_factor := (v_target_power - v_lower_power)::DECIMAL / (v_upper_power - v_lower_power)::DECIMAL;
            RETURN QUERY SELECT 
                v_lower_hashrate + (v_upper_hashrate - v_lower_hashrate) * v_interpolation_factor,
                v_target_power;
        END IF;
    ELSE
        -- Aucun point trouvé, retourner NULL
        RETURN QUERY SELECT NULL::DECIMAL(15,2), NULL::INTEGER;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Message de confirmation
SELECT 'Fonctions SQL corrigées avec succès!' as status; 