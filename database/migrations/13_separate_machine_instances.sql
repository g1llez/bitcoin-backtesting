-- Migration pour séparer les instances de machines avec quantity > 1
-- Cette migration transforme les instances multiples en instances individuelles

-- Créer une table temporaire pour stocker les nouvelles instances
CREATE TEMP TABLE temp_new_instances AS
SELECT 
    nextval('site_machine_instances_id_seq') as new_id,
    site_id,
    template_id,
    1 as quantity,
    custom_name,
    notes,
    optimal_ratio,
    ratio_type,
    created_at,
    updated_at
FROM site_machine_instances 
WHERE quantity > 1;

-- Insérer les nouvelles instances individuelles
INSERT INTO site_machine_instances (
    id, site_id, template_id, quantity, custom_name, notes, 
    optimal_ratio, ratio_type, created_at, updated_at
)
SELECT 
    new_id, site_id, template_id, quantity, custom_name, notes,
    optimal_ratio, ratio_type, created_at, updated_at
FROM temp_new_instances;

-- Supprimer les anciennes instances avec quantity > 1
DELETE FROM site_machine_instances 
WHERE quantity > 1;

-- Nettoyer la table temporaire
DROP TABLE temp_new_instances;

-- Message de confirmation
SELECT 'Instances de machines séparées avec succès!' as status; 