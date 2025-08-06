-- Migration pour corriger la séparation des instances
-- Créer 2 instances individuelles pour remplacer l'instance avec quantity=2

-- Supprimer l'instance actuelle du site 3 (qui était l'ancienne instance avec quantity=2)
DELETE FROM site_machine_instances WHERE site_id = 3;

-- Créer 2 instances individuelles pour le site 3
INSERT INTO site_machine_instances (
    site_id, template_id, quantity, custom_name, notes, 
    optimal_ratio, ratio_type, created_at, updated_at
) VALUES 
(3, 1, 1, 'Antminer S19 Pro #1', null, 0.85, 'manual', NOW(), NOW()),
(3, 1, 1, 'Antminer S19 Pro #2', null, 0.85, 'manual', NOW(), NOW());

-- Message de confirmation
SELECT 'Instances corrigées avec succès!' as status; 