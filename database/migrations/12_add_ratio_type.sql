-- Migration pour ajouter la colonne ratio_type aux instances de machines
-- Cette colonne permet de distinguer entre ratio manuel, optimal et nominal

-- Ajouter la colonne ratio_type à la table site_machine_instances
ALTER TABLE site_machine_instances 
ADD COLUMN ratio_type VARCHAR(10) DEFAULT 'nominal';

-- Mettre à jour les données existantes
-- Si optimal_ratio est NULL, c'est nominal
-- Si optimal_ratio a une valeur, c'est manuel (par défaut)
UPDATE site_machine_instances 
SET ratio_type = CASE 
    WHEN optimal_ratio IS NULL THEN 'nominal'
    ELSE 'manual'
END;

-- Commentaire pour documenter l'usage de cette colonne
COMMENT ON COLUMN site_machine_instances.ratio_type IS 
'Type de ratio appliqué: manual, optimal, ou nominal';

-- Message de confirmation
SELECT 'Colonne ratio_type ajoutée avec succès à site_machine_instances!' as status; 