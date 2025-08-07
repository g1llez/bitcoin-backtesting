-- Migration 16: Ajouter le champ global_optimal_ratio à la table site_machine_instances
-- Date: 2024-01-XX
-- Description: Ajoute le champ global_optimal_ratio pour stocker les ratios optimaux globaux

-- Ajouter la colonne global_optimal_ratio
ALTER TABLE site_machine_instances 
ADD COLUMN global_optimal_ratio DECIMAL(5, 3) NULL;

-- Mettre à jour les commentaires pour clarifier les types de ratio
COMMENT ON COLUMN site_machine_instances.ratio_type IS 'Type de ratio: manual, optimal, nominal, global, disabled';
COMMENT ON COLUMN site_machine_instances.global_optimal_ratio IS 'Ratio optimal global (après optimisation globale)';
