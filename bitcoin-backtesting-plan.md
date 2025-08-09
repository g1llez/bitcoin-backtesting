# Plan de développement - Solution de Backtesting Bitcoin

## Objectif principal
Développer une solution de backtesting pour évaluer l'efficacité des machines Bitcoin entre les paiements d'électricité, avec un focus sur l'optimisation des paramètres de mining selon les conditions de marché.

## Configuration fixe - Paramètres visibles en tout temps

| Catégorie | Paramètre | Valeur actuelle | Unité |
|-----------|-----------|-----------------|-------|
| **Machine Bitcoin** | Modèle | Antminer S19 | - |
| | Hashrate nominal | 95 | TH/s |
| | Consommation nominale | 3250 | W |
| | Efficacité de base | 34.2 | J/TH |
| | Ratio d'ajustement | 0.8 | - |
| **Électricité Québec** | Premier palier (0-40 kWh) | 0.0738 | $/kWh |
| | Deuxième palier (>40 kWh) | 0.1089 | $/kWh |
| | Période facturation | Mensuelle | - |
| | Coûts fixes | 25.00 | $/mois |
| **Marché** | Devise | CAD | - |
| | Taux USD/CAD | 1.35 | - |
| **Backtesting** | Période début | 2024-01-01 | - |
| | Période fin | 2024-12-31 | - |
| | Fréquence réévaluation | Quotidienne | - |
| | Stratégie ajustement | Automatique | - |

## État actuel de l'application

### ✅ Infrastructure complète (TERMINÉ)
- **Docker Compose** : 3 services (PostgreSQL, API FastAPI, Frontend Nginx)
- **Base de données** : Modèles SQLAlchemy complets
- **API Backend** : FastAPI avec routes complètes
- **Frontend** : Interface web moderne avec Bootstrap et Chart.js

### ✅ Modèles de données (TERMINÉ)
- **BitcoinPrice** : Prix historiques BTC (USD/CAD)
- **FppsData** : Données FPPS et difficulté réseau
- **MachineTemplate** : Templates de machines (S19, S21, etc.)
- **MachineEfficiencyCurve** : Courbes d'efficacité mesurées
- **MiningSite** : Sites de minage avec tarifs électriques
- **SiteMachineInstance** : Instances de machines dans les sites
- **BacktestResult** : Résultats de backtesting
- **DailySimulation** : Simulations quotidiennes détaillées
- **AppConfig** : Configuration globale

### ✅ API Routes implémentées (TERMINÉ)
- **Machines** : CRUD templates et instances
- **Sites** : Gestion des sites de minage
- **Efficiency** : Courbes d'efficacité et optimisation
- **Market Data** : Prix Bitcoin et données FPPS
- **Backtest** : Endpoints présents; moteur de calcul et persistance des résultats à finaliser
- **Configuration** : Paramètres globaux

### ✅ Interface utilisateur (TERMINÉ)
- **Navigation** : Sites, machines, backtest, résultats
- **Gestion des sites** : CRUD complet
- **Gestion des machines** : Templates et instances
- **Courbes d'efficacité** : Visualisation et édition
- **Optimisation** : Calculs automatiques des ratios optimaux (affichage J/TH au lieu de TH/s/W)

### ✅ Politiques de fallback
- Électricité: si un site n'a pas de tarifs, complétion implicite depuis la config globale; si des champs restent manquants, coût=0 (pas d'erreur).
- Efficience: si des données d'efficacité sont manquantes pour un ratio, fallback nominal (hashrate/power du template × ratio) pour éviter les erreurs.
- **Thèmes** : Dark/Light/Colorful
- **Responsive** : Mobile et desktop

## Architecture actuelle

### Structure du projet
```
bitcoin-backtesting/
├── docker-compose.yml          # ✅ Infrastructure Docker
├── api/
│   ├── Dockerfile             # ✅ API FastAPI
│   ├── requirements.txt       # ✅ Dépendances Python
│   └── app/
│       ├── main.py           # ✅ Point d'entrée API
│       ├── database.py       # ✅ Configuration DB
│       ├── models/
│       │   ├── models.py     # ✅ Modèles SQLAlchemy
│       │   └── schemas.py    # ✅ Schémas Pydantic
│       ├── routes/           # ✅ Routes API complètes (CORS configurable, fallback électricité optionnel)
│       └── services/         # ✅ Services métier
├── frontend/
│   ├── index.html           # ✅ Interface principale
│   ├── app.js              # ✅ Logique JavaScript
│   ├── styles.css          # ✅ Styles CSS
│   └── test-layout.html    # ✅ Tests d'interface
├── database/
│   └── migrations/         # ✅ Scripts de migration
└── docs/                   # 📁 Documentation
```

## Fonctionnalités implémentées

### ✅ Gestion des sites de minage
- Création/modification/suppression de sites
- Configuration des tarifs électriques québécois
- Gestion des tokens Braiins (pour données réelles)

### ✅ Gestion des machines
- Templates de machines (S19, S21, etc.)
- Instances de machines dans les sites
- Courbes d'efficacité mesurées
- Interpolation automatique des ratios

### ✅ Optimisation des ratios
- Calcul automatique du ratio optimal économique
- Calcul du ratio optimal en satoshis
- Analyse de sensibilité des ratios
- Visualisation des courbes d'efficacité

### ✅ Données de marché
- Prix Bitcoin historiques (USD/CAD)
- Données FPPS et difficulté réseau
- Cache automatique des données
- Import de données manquantes
 - Exposition des prix CAD et USD; utilisation de la devise du site (`preferred_currency`) dans les calculs et réponses API

### ✅ Observabilité
- Endpoint Prometheus `/metrics` (métriques requêtes):
  - `api_requests_total` (méthode/chemin/statut)
  - `api_request_duration_seconds` (latence)
  - Compteurs prévus pour les caches (efficiency)

### ✅ Interface utilisateur avancée
- Navigation par phases de backtesting
- Thèmes visuels (Dark/Light/Colorful)
- Graphiques interactifs (Chart.js)
- Interface responsive

## Prochaines étapes - Logique de backtesting

### 🎯 Phase 1: Finalisation du moteur de backtesting
1. **Implémentation complète de la logique de calcul**
   - Calcul quotidien des revenus (hashrate × FPPS × 24h / difficulté)
   - Calcul des coûts électriques (paliers québécois)
   - Calcul du profit net et ROI

2. **Optimisation des algorithmes**
   - Beam search (largeur configurable) au lieu de combinaisons exhaustives
   - Limiter aux N meilleurs ratios par machine + raffinement local
   - Early break avec bornes supérieures de profit
   - Mémoïsation locale des efficacités (ratio→hashrate/power)
   - Paramètres de contrôle: max_runtime_s, max_combinations, beam_width, top_ratios_per_machine

3. **Métriques d'analyse avancées**
   - Volatilité des profits
   - Périodes de rentabilité/pertes
   - Comparaison de stratégies

### 🎯 Phase 2: Interface de backtesting
1. **Dashboard de backtesting**
   - Configuration des paramètres de test
   - Lancement des simulations
   - Suivi en temps réel

2. **Visualisations des résultats**
   - Évolution des profits dans le temps
   - Comparaison des stratégies
   - Graphiques d'analyse de sensibilité

3. **Export et reporting**
   - Export des résultats en CSV/PDF
   - Rapports détaillés
   - Partage des configurations

### 🎯 Phase 3: Fonctionnalités avancées
1. **Données environnementales**
   - Impact de la température sur l'efficacité
   - Coûts de refroidissement
   - Modélisation saisonnière

2. **Données de maintenance**
   - Coûts de maintenance
   - Temps d'arrêt
   - Dégradation dans le temps

3. **Analyse fiscale**
   - Impôts sur les gains
   - Déductions d'entreprise
   - TVQ/TPS sur l'électricité

## Questions techniques à résoudre

### 🔍 Sources de données
- ✅ API Bitcoin historiques (implémentée)
- ✅ Données FPPS (implémentée)
- ❓ Spécifications détaillées des machines (partiellement implémentée)

### 🔍 Modélisation
- ✅ Relation ratio d'ajustement/consommation (implémentée)
- ❓ Impact des variations de température
- ❓ Dégradation de l'efficacité dans le temps

### 🔍 Optimisation
- ✅ Algorithmes d'optimisation des ratios (première version)
- 🔧 Améliorations de performance (beam search, cache, limites de temps/volume)
- ❓ Contraintes techniques des machines
- ❓ Fréquence de réévaluation optimale

## Métriques de succès

### 📊 Fonctionnelles
- [ ] Calculs de backtesting précis et validés
- [ ] Interface utilisateur intuitive et performante
- [ ] Intégration complète des données de marché

### 📊 Techniques
- [ ] Performance optimale (temps de calcul < 30s) avec paramètres de contrôle (max_runtime_s, max_combinations)
- [ ] Fiabilité des données (99.9% uptime)
- [ ] Scalabilité (support multi-machines)

### 📊 Business
- [ ] Précision des prédictions de rentabilité
- [ ] Facilité d'utilisation pour les mineurs
- [ ] ROI positif pour les utilisateurs 