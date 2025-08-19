-- Migration 17: Ajouter les champs accepted_shares_24h pour le calcul de revenus basé sur les shares
-- Date: 2024-01-XX
-- Description: Ajoute les champs accepted_shares_24h pour remplacer l'API Braiins dans le calcul de revenus

-- Ajouter la colonne accepted_shares_24h à machine_templates
ALTER TABLE machine_templates 
ADD COLUMN accepted_shares_24h BIGINT NULL;

-- Ajouter la colonne accepted_shares_24h à mining_sites
ALTER TABLE mining_sites 
ADD COLUMN accepted_shares_24h BIGINT NULL;

-- Ajouter la colonne accepted_shares_24h à app_config (si elle n'existe pas déjà)
INSERT INTO app_config (key, value, description) VALUES
('accepted_shares_24h', NULL, 'Shares acceptées par jour globales (fallback pour le calcul de revenus)')
ON CONFLICT (key) DO NOTHING;

-- Mettre à jour les commentaires pour clarifier l'utilisation
COMMENT ON COLUMN machine_templates.accepted_shares_24h IS 'Shares acceptées par jour pour cette machine spécifique (priorité 1)';
COMMENT ON COLUMN mining_sites.accepted_shares_24h IS 'Shares acceptées par jour pour ce site (fallback, priorité 2)';
COMMENT ON COLUMN app_config.value IS 'Valeur de configuration (pour accepted_shares_24h: shares globales, priorité 3)';

-- Message de confirmation
SELECT 'Migration 17: Champs accepted_shares_24h ajoutés avec succès!' as status;
