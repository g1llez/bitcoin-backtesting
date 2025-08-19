-- Migration 18: Restructurer les accepted shares selon la logique Machine → Template
-- Date: 2024-01-XX
-- Description: Restructure les accepted shares pour utiliser Machine Instance → Machine Template au lieu de Site → Global

-- Ajouter la colonne accepted_shares_24h à site_machine_instances
ALTER TABLE site_machine_instances 
ADD COLUMN accepted_shares_24h BIGINT NULL;

-- Supprimer la colonne accepted_shares_24h de mining_sites (plus utilisée)
ALTER TABLE mining_sites 
DROP COLUMN IF EXISTS accepted_shares_24h;

-- Supprimer la configuration globale accepted_shares_24h (plus utilisée)
DELETE FROM app_config WHERE key = 'accepted_shares_24h';

-- Mettre à jour les commentaires pour clarifier la nouvelle logique
COMMENT ON COLUMN machine_templates.accepted_shares_24h IS 'Shares acceptées par jour par défaut pour ce modèle de machine (fallback)';
COMMENT ON COLUMN site_machine_instances.accepted_shares_24h IS 'Shares acceptées par jour pour cette instance spécifique (priorité 1)';

-- Message de confirmation
SELECT 'Migration 18: Restructuration des accepted shares terminée avec succès!' as status;
