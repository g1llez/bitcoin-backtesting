-- Migration pour changer le prix de USD vers CAD
-- Supprimer l'ancienne colonne price_usd et ajouter price_cad

-- Supprimer l'ancienne colonne price_usd
ALTER TABLE mining_machines DROP COLUMN IF EXISTS price_usd;

-- Ajouter la nouvelle colonne price_cad
ALTER TABLE mining_machines ADD COLUMN price_cad DECIMAL(10,2);

-- Mettre à jour les données existantes (si nécessaire)
-- UPDATE mining_machines SET price_cad = 1000.00 WHERE model = 'Antminer S19 Pro';
-- UPDATE mining_machines SET price_cad = 1750.00 WHERE model = 'Antminer S21';
-- UPDATE mining_machines SET price_cad = 1250.00 WHERE model = 'Antminer S19 XP';

-- Message de confirmation
SELECT 'Migration vers CAD terminée!' as status; 