-- Migration pour corriger la précision des colonnes d'électricité
-- Les valeurs actuelles sont tronquées à 4 décimales, on veut plus de précision

-- Modifier la précision des colonnes d'électricité
ALTER TABLE mining_sites 
ALTER COLUMN electricity_tier1_rate TYPE numeric(8,5),
ALTER COLUMN electricity_tier2_rate TYPE numeric(8,5);

-- Mettre à jour les valeurs avec plus de précision
UPDATE mining_sites 
SET electricity_tier1_rate = 0.07708,
    electricity_tier2_rate = 0.11891
WHERE id = 3;

-- Vérifier les autres sites et les mettre à jour si nécessaire
UPDATE mining_sites 
SET electricity_tier1_rate = 0.07708,
    electricity_tier2_rate = 0.11891
WHERE electricity_tier1_rate = 0.0771 OR electricity_tier2_rate = 0.1189; 