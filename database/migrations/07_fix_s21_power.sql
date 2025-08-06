-- Migration pour corriger la puissance nominale de la S21
-- Changer de 3010W à 3500W

UPDATE mining_machines 
SET power_nominal = 3500 
WHERE model = 'Antminer S21';

-- Vérifier la mise à jour
SELECT model, power_nominal, hashrate_nominal 
FROM mining_machines 
WHERE model = 'Antminer S21';

-- Message de confirmation
SELECT 'Puissance nominale de la S21 corrigée de 3010W à 3500W!' as status; 