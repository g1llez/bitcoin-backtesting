-- Migration pour ajouter la colonne optimal_ratio aux instances de machines
-- Cette colonne permet de stocker un ratio d'ajustement manuel appliqué à une instance

-- Ajouter la colonne optimal_ratio à la table site_machine_instances
ALTER TABLE site_machine_instances 
ADD COLUMN optimal_ratio DECIMAL(5,3);

-- Commentaire pour documenter l'usage de cette colonne
COMMENT ON COLUMN site_machine_instances.optimal_ratio IS 
'Ratio d''ajustement manuel appliqué à cette instance (0.5 à 1.5). NULL = ratio automatique/optimal';

-- Message de confirmation
SELECT 'Colonne optimal_ratio ajoutée avec succès à site_machine_instances!' as status; 