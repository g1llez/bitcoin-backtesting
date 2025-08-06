# 📋 Sommaire du Système de Backtest Bitcoin

## 🎯 Objectif Principal
Créer un système de backtest qui ajuste dynamiquement l'agressivité du mining selon les conditions de marché et le temps restant, pour maximiser le profit net en tenant compte du ROI des machines.

## 🏗️ Composants du Système

### **1. Données Requises**
- **Prix Bitcoin historique** (pour calculer SD)
- **FPPS historique** (pour calculer les revenus)
- **Données d'efficacité des machines** (courbes d'efficacité)
- **Configuration des sites** (prix électricité, machines)

### **2. Calcul de la Volatilité (SD Mixte)**
```
SD_final = (SD_4ans * 0.6) + (SD_1an * 0.4)
```
- **SD 4 ans** : Capture cycles de halving et tendances longues
- **SD 1 an** : Capture volatilité récente

### **3. Calcul du Profit Visé**
```
Profit_visé_annuel = Coût_total_machines / Période_ROI_mois * 12
Profit_visé_cycle = Profit_visé_annuel / (12 / Intervalle_paiement_mois)
```

### **4. Logique d'Ajustement Quotidien**
1. **Estimation du profit du prochain cycle** : [min, max] basé sur SD
2. **Capital actuel** dans le compte
3. **Profit minimal garanti** = Capital + Profit_min_estimé
4. **Comparaison** avec Profit_visé_cycle

### **5. Décisions d'Agressivité**
- **Agressif** : Profit_min_garanti > Profit_visé_cycle
- **Modéré** : Profit_min_garanti > (Profit_visé_cycle * 0.5)
- **Conservateur** : Profit_min_garanti < (Profit_visé_cycle * 0.5)

## 📊 Paramètres Configurables

### **Paramètres de Test**
- Date début/fin du backtest
- Intervalle de paiement (mois)
- Période ROI visée (mois, défaut: 36)

### **Paramètres d'Ajustement**
- Taux d'agressivité de départ (ex: 1.2)
- Poids SD 4ans (défaut: 0.6)
- Poids SD 1an (défaut: 0.4)

### **Sélection des Sites**
- Sites à inclure dans le test
- Machines configurées dans chaque site

## 🔄 Cycle de Fonctionnement

### **Phase 1 : Préparation**
- Vérification des données historiques Bitcoin/FPPS
- Import des données manquantes
- Validation de la configuration

### **Phase 2 : Simulation**
- Simulation jour par jour
- Calcul quotidien de l'agressivité
- Accumulation des profits entre cycles
- Ajustement des ratios selon les conditions

### **Phase 3 : Résultats**
- Profit total final
- Ratio vs simulation sans ajustement
- Analyse des performances par cycle
- Graphiques d'évolution

## 📈 Métriques de Performance

### **Métriques Principales**
- **Profit total final** (avec ajustement)
- **Ratio de performance** = Profit_ajusté / Profit_base
- **ROI effectif** vs ROI visé

### **Métriques Détaillées**
- Performance par cycle de paiement
- Évolution de l'agressivité dans le temps
- Impact des conditions de marché
- Analyse des décisions d'ajustement

## 🚀 Plan de Déploiement

### **Phase 1 : Interface de Configuration**
- Interface de paramétrage du backtest
- Sélection des sites/machines
- Validation des données requises

### **Phase 2 : API Backend**
- Endpoints pour la simulation
- Calculs de SD et ajustements
- Stockage des résultats

### **Phase 3 : Interface de Résultats**
- Affichage des résultats
- Graphiques d'évolution
- Analyse comparative

### **Phase 4 : Optimisation**
- Ajustement des algorithmes
- Amélioration des performances
- Tests et validation

## 📝 Notes de Développement

### **Priorités**
1. Interface de configuration simple et intuitive
2. Calculs de SD robustes et performants
3. Simulation précise jour par jour
4. Visualisation claire des résultats

### **Risques Identifiés**
- Performance des calculs sur de longues périodes
- Précision des estimations de volatilité
- Gestion de la mémoire pour les données historiques

### **Améliorations Futures**
- Machine learning pour optimiser les paramètres
- Backtesting sur plusieurs stratégies simultanément
- Intégration avec des APIs de trading

---

**Ce document servira de référence pour le développement et le déploiement du système de backtest.**

*Dernière mise à jour : $(date)* 