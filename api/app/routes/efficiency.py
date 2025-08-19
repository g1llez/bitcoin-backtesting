from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from decimal import Decimal

from ..database import get_db
from ..models import models
from ..models.schemas import MachineEfficiencyCurve, MachineEfficiencyCurveCreate, MachineEfficiencyCurveUpdate

router = APIRouter()

@router.get("/efficiency/machines/{machine_id}", response_model=List[MachineEfficiencyCurve])
async def get_machine_efficiency_curves(machine_id: int, db: Session = Depends(get_db)):
    """Récupérer toutes les courbes d'efficacité d'un template de machine"""
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    curves = db.query(models.MachineEfficiencyCurve).filter(
        models.MachineEfficiencyCurve.machine_id == machine_id
    ).order_by(models.MachineEfficiencyCurve.power_consumption).all()
    
    return curves

@router.post("/efficiency/curves", response_model=MachineEfficiencyCurve)
async def create_efficiency_curve(curve: MachineEfficiencyCurveCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle courbe d'efficacité"""
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == curve.machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Vérifier si la courbe existe déjà pour cette puissance
    existing_curve = db.query(models.MachineEfficiencyCurve).filter(
        models.MachineEfficiencyCurve.machine_id == curve.machine_id,
        models.MachineEfficiencyCurve.power_consumption == curve.power_consumption
    ).first()
    
    if existing_curve:
        raise HTTPException(status_code=400, detail="Une courbe d'efficacité existe déjà pour cette puissance")
    
    db_curve = models.MachineEfficiencyCurve(**curve.dict())
    db.add(db_curve)
    db.commit()
    db.refresh(db_curve)
    return db_curve

@router.put("/efficiency/curves/{curve_id}", response_model=MachineEfficiencyCurve)
async def update_efficiency_curve(
    curve_id: int, 
    curve_update: MachineEfficiencyCurveUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour une courbe d'efficacité"""
    db_curve = db.query(models.MachineEfficiencyCurve).filter(
        models.MachineEfficiencyCurve.id == curve_id
    ).first()
    
    if not db_curve:
        raise HTTPException(status_code=404, detail="Courbe d'efficacité non trouvée")
    
    # Mettre à jour les champs fournis
    update_data = curve_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_curve, field, value)
    
    db.commit()
    db.refresh(db_curve)
    return db_curve

@router.delete("/efficiency/curves/{curve_id}")
async def delete_efficiency_curve(curve_id: int, db: Session = Depends(get_db)):
    """Supprimer une courbe d'efficacité"""
    db_curve = db.query(models.MachineEfficiencyCurve).filter(
        models.MachineEfficiencyCurve.id == curve_id
    ).first()
    
    if not db_curve:
        raise HTTPException(status_code=404, detail="Courbe d'efficacité non trouvée")
    
    db.delete(db_curve)
    db.commit()
    return {"message": "Courbe d'efficacité supprimée avec succès"}

@router.get("/efficiency/machines/{machine_id}/ratio/{adjustment_ratio}")
async def get_machine_efficiency_at_ratio(
    machine_id: int, 
    adjustment_ratio: Decimal, 
    db: Session = Depends(get_db)
):
    """Récupérer l'efficacité d'un template à un ratio spécifique (avec interpolation)"""
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Utiliser la fonction SQL pour l'interpolation
    result = db.execute(
        text("SELECT * FROM get_machine_efficiency_interpolated(:machine_id, :ratio)"),
        {"machine_id": machine_id, "ratio": adjustment_ratio}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Aucune donnée d'efficacité trouvée pour ce ratio")
    
    return {
        "machine_id": machine_id,
        "adjustment_ratio": adjustment_ratio,
        "effective_hashrate": result[0],
        "power_consumption": result[1]
    }

@router.get("/efficiency/machines/{machine_id}/power/{power_consumption}")
async def get_machine_efficiency_at_power(
    machine_id: int, 
    power_consumption: int, 
    db: Session = Depends(get_db)
):
    """Récupérer l'efficacité d'un template à une puissance spécifique et calculer le ratio"""
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Calculer le ratio automatiquement
    ratio_result = db.execute(
        text("SELECT calculate_adjustment_ratio(:machine_id, :power)"),
        {"machine_id": machine_id, "power": power_consumption}
    ).fetchone()
    
    if not ratio_result:
        raise HTTPException(status_code=404, detail="Impossible de calculer le ratio")
    
    adjustment_ratio = ratio_result[0]
    
    # Utiliser la fonction SQL pour l'interpolation
    efficiency_result = db.execute(
        text("SELECT * FROM get_machine_efficiency_interpolated(:machine_id, :ratio)"),
        {"machine_id": machine_id, "ratio": adjustment_ratio}
    ).fetchone()
    
    if not efficiency_result:
        raise HTTPException(status_code=404, detail="Aucune donnée d'efficacité trouvée")
    
    return {
        "machine_id": machine_id,
        "power_consumption": power_consumption,
        "adjustment_ratio": adjustment_ratio,
        "effective_hashrate": efficiency_result[0],
        "calculated_power": efficiency_result[1]
    } 

def get_market_and_electricity_data(db: Session):
    """
    Récupère les données de marché et d'électricité communes aux deux endpoints
    """
    # Récupérer les données de marché depuis le cache
    from ..services.market_cache import MarketCacheService
    cache_service = MarketCacheService(db)
    market_data = cache_service.get_market_data()
    bitcoin_price = market_data["bitcoin_price"] if market_data["bitcoin_price"] is not None else None
    fpps_rate = market_data["fpps_rate"] if market_data["fpps_rate"] is not None else None
    
    # Récupérer les taux d'électricité depuis la configuration
    tier1_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_rate").first()
    tier2_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier2_rate").first()
    tier1_limit_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_limit").first()
    
    electricity_tier1_rate = float(tier1_config.value) if (tier1_config and tier1_config.value) else None
    electricity_tier2_rate = float(tier2_config.value) if (tier2_config and tier2_config.value) else None
    electricity_tier1_limit = int(tier1_limit_config.value) if (tier1_limit_config and tier1_limit_config.value) else None
    
    return {
        "bitcoin_price": bitcoin_price,
        "fpps_rate": fpps_rate,
        "electricity_tier1_rate": electricity_tier1_rate,
        "electricity_tier2_rate": electricity_tier2_rate,
        "electricity_tier1_limit": electricity_tier1_limit
    }

@router.get("/efficiency/machines/{machine_id}/optimal-ratio")
def find_optimal_adjustment_ratio(
    machine_id: int,
    db: Session = Depends(get_db)
):
    """
    Trouve le ratio d'ajustement optimal pour maximiser les profits
    en utilisant une approche en deux étapes : globale (0.05) puis fine (0.01)
    """
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Récupérer les données communes
    common_data = get_market_and_electricity_data(db)
    bitcoin_price = common_data["bitcoin_price"]
    fpps_rate = common_data["fpps_rate"]
    electricity_tier1_rate = common_data["electricity_tier1_rate"]
    electricity_tier2_rate = common_data["electricity_tier2_rate"]
    electricity_tier1_limit = common_data["electricity_tier1_limit"]
    
    optimal_ratio = None
    max_profit = float('-inf')
    results = []
    
    # ÉTAPE 1: Optimisation globale avec incréments de 0.05
    global_optimal_ratio = None
    global_max_profit = float('-inf')
    
    # Tester des ratios de 0.5 à 1.5 par incréments de 0.05
    for ratio in [round(x * 0.05, 2) for x in range(10, 31)]:  # 0.5 à 1.5
        try:
            # Obtenir l'efficacité pour ce ratio
            result = db.execute(text("""
                SELECT effective_hashrate, power_consumption 
                FROM get_machine_efficiency_interpolated(:machine_id, :ratio)
            """), {"machine_id": machine_id, "ratio": ratio})
            
            efficiency = result.fetchone()
            if efficiency and efficiency[0] is not None:
                hashrate = float(efficiency[0])
                power = int(efficiency[1])
                
                # Calculer les revenus basés sur les accepted shares
                daily_revenue = None
                sats_per_hour = None
                
                # Vérifier si la machine a des accepted shares configurées
                if machine.accepted_shares_24h is not None:
                    try:
                        # Récupérer la difficulté du réseau
                        import requests
                        difficulty_response = requests.get("https://blockchain.info/q/getdifficulty", timeout=10)
                        difficulty_response.raise_for_status()
                        network_difficulty = float(difficulty_response.text)
                        
                        # Récupérer la récompense de bloc
                        block_reward_response = requests.get("https://blockchain.info/q/bcperblock", timeout=10)
                        block_reward_response.raise_for_status()
                        coinbase_reward = float(block_reward_response.text)
                        
                        # Calculer le revenu avec la formule CRC = C × S/D
                        # Répartir les shares proportionnellement au hashrate de ce ratio
                        machine_shares = float(machine.accepted_shares_24h) * (hashrate / float(machine.hashrate_nominal))
                        btc_earned_24h = (coinbase_reward * machine_shares) / network_difficulty
                        
                        if bitcoin_price is not None:
                            daily_revenue = btc_earned_24h * bitcoin_price
                            # Calculer les sats/heure pour l'affichage
                            sats_per_hour = int((btc_earned_24h * 100000000) / 24)
                    except Exception:
                        # En cas d'erreur, revenu non calculable
                        daily_revenue = None
                        sats_per_hour = None
                else:
                    # Pas d'accepted shares => pas de revenus calculables
                    daily_revenue = None
                    sats_per_hour = None
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                # Calculer le coût avec les paliers
                if electricity_tier1_rate is None or electricity_tier2_rate is None or electricity_tier1_limit is None:
                    daily_electricity_cost = None
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue is None or daily_electricity_cost is None:
                    daily_profit = None
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                # Calculer l'efficacité technique (TH/s par Watt)
                efficiency_ratio = hashrate / power if power > 0 else 0
                
                result_data = {
                    "adjustment_ratio": ratio,
                    "effective_hashrate": hashrate,
                    "power_consumption": power,
                    "efficiency_th_per_watt": round(efficiency_ratio, 6),
                    "efficiency_j_per_th": round(power / hashrate, 2) if hashrate > 0 else 0,
                    "sats_per_hour": sats_per_hour,
                    "daily_revenue": "N/A" if daily_revenue is None else round(daily_revenue, 2),
                    "daily_electricity_cost": round(daily_electricity_cost, 2) if daily_electricity_cost is not None else None,
                    "daily_profit": "N/A" if daily_profit is None else round(daily_profit, 2)
                }
                results.append(result_data)
                
                # Mettre à jour l'optimal global si ce ratio est plus profitable
                if daily_profit > global_max_profit:
                    global_max_profit = daily_profit
                    global_optimal_ratio = ratio
                    
        except Exception as e:
            continue
    
    # Si aucun ratio optimal global n'a été trouvé, utiliser le ratio avec le meilleur hashrate
    if global_optimal_ratio is None and results:
        # Trouver le ratio avec le meilleur hashrate
        best_hashrate_result = max(results, key=lambda x: x['effective_hashrate'])
        global_optimal_ratio = best_hashrate_result['adjustment_ratio']
        global_max_profit = best_hashrate_result.get('daily_profit', None)
    
    # Si toujours aucun résultat, renvoyer une erreur explicite
    if global_optimal_ratio is None:
        raise HTTPException(status_code=400, detail="Impossible de déterminer un ratio optimal avec les données disponibles")
    
    
    # ÉTAPE 2: Optimisation fine avec incréments de 0.01 autour du meilleur ratio global
    
    # Définir la plage fine autour du ratio optimal global (±0.10)
    fine_range = 0.10
    fine_step = 0.01
    
    # Calculer les bornes de la recherche fine
    fine_start = max(0.5, global_optimal_ratio - fine_range)
    fine_end = min(1.5, global_optimal_ratio + fine_range)
    
    # Générer les ratios pour la recherche fine
    fine_ratios = [round(fine_start + i * fine_step, 2) for i in range(int((fine_end - fine_start) / fine_step) + 1)]
    
    # Réinitialiser pour la recherche fine
    optimal_ratio = global_optimal_ratio
    max_profit = global_max_profit
    
    # Recherche fine
    for ratio in fine_ratios:
        try:
            # Obtenir l'efficacité pour ce ratio
            result = db.execute(text("""
                SELECT effective_hashrate, power_consumption 
                FROM get_machine_efficiency_interpolated(:machine_id, :ratio)
            """), {"machine_id": machine_id, "ratio": ratio})
            
            efficiency = result.fetchone()
            if efficiency and efficiency[0] is not None:
                hashrate = float(efficiency[0])
                power = int(efficiency[1])
                
                # Calculer les revenus basés sur les accepted shares
                daily_revenue = None
                sats_per_hour = None
                
                # Vérifier si la machine a des accepted shares configurées
                if machine.accepted_shares_24h is not None:
                    try:
                        # Récupérer la difficulté du réseau
                        import requests
                        difficulty_response = requests.get("https://blockchain.info/q/getdifficulty", timeout=10)
                        difficulty_response.raise_for_status()
                        network_difficulty = float(difficulty_response.text)
                        
                        # Récupérer la récompense de bloc
                        block_reward_response = requests.get("https://blockchain.info/q/bcperblock", timeout=10)
                        block_reward_response.raise_for_status()
                        coinbase_reward = float(block_reward_response.text)
                        
                        # Calculer le revenu avec la formule CRC = C × S/D
                        # Répartir les shares proportionnellement au hashrate de ce ratio
                        machine_shares = float(machine.accepted_shares_24h) * (hashrate / float(machine.hashrate_nominal))
                        btc_earned_24h = (coinbase_reward * machine_shares) / network_difficulty
                        
                        if bitcoin_price is not None:
                            daily_revenue = btc_earned_24h * bitcoin_price
                            # Calculer les sats/heure pour l'affichage
                            sats_per_hour = int((btc_earned_24h * 100000000) / 24)
                    except Exception:
                        # En cas d'erreur, revenu non calculable
                        daily_revenue = None
                        sats_per_hour = None
                else:
                    # Pas d'accepted shares => pas de revenus calculables
                    daily_revenue = None
                    sats_per_hour = None
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                # Calculer le coût avec les paliers
                if electricity_tier1_rate is None or electricity_tier2_rate is None or electricity_tier1_limit is None:
                    daily_electricity_cost = None
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue is None or daily_electricity_cost is None:
                    daily_profit = None
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                # Calculer l'efficacité technique (TH/s par Watt)
                efficiency_ratio = hashrate / power if power > 0 else 0
                
                result_data = {
                    "adjustment_ratio": ratio,
                    "effective_hashrate": hashrate,
                    "power_consumption": power,
                    "efficiency_th_per_watt": round(efficiency_ratio, 6),
                    "efficiency_j_per_th": round(power / hashrate, 2) if hashrate > 0 else 0,
                    "sats_per_hour": sats_per_hour,
                    "daily_revenue": round(daily_revenue, 2) if daily_revenue is not None else None,
                    "daily_electricity_cost": round(daily_electricity_cost, 2) if daily_electricity_cost is not None else None,
                    "daily_profit": round(daily_profit, 2) if daily_profit is not None else None
                }
                results.append(result_data)
                
                # Mettre à jour l'optimal si ce ratio est plus profitable
                if daily_profit > max_profit:
                    max_profit = daily_profit
                    optimal_ratio = ratio
                    
        except Exception as e:
            continue
    
    
    # Déterminer le message selon la disponibilité des shares
    if max_profit == "N/A" or max_profit is None:
        message = "⚠️ Aucun profit calculable car pas d'accepted shares configurées. Configurez des shares pour voir les profits optimaux."
        shares_warning = True
    else:
        message = f"Analyse des ratios terminée. Ratio optimal: {optimal_ratio}"
        shares_warning = False
    
    return {
        "machine_id": machine_id,
        "optimal_ratio": optimal_ratio,
        "max_daily_profit": "N/A" if max_profit == "N/A" else (round(max_profit, 2) if max_profit is not None else None),
        "all_results": results,
        "message": message,
        "shares_warning": shares_warning
    }

def get_available_ratios(machine_id: int, db: Session):
    """
    Trouve les ratios minimum et maximum disponibles pour une machine
    en testant différents ratios et en vérifiant lesquels retournent des données
    """
    available_ratios = []
    
    # Tester des ratios de 0.5 à 1.5 par incréments de 0.05
    for ratio in [round(x * 0.05, 2) for x in range(10, 31)]:  # 0.5 à 1.5
        try:
            result = db.execute(text("""
                SELECT effective_hashrate, power_consumption 
                FROM get_machine_efficiency_interpolated(:machine_id, :ratio)
            """), {"machine_id": machine_id, "ratio": ratio})
            
            efficiency = result.fetchone()
            if efficiency and efficiency[0] is not None:
                available_ratios.append(ratio)
                
        except Exception as e:
            continue
    
    if available_ratios:
        return {
            "min_ratio": min(available_ratios),
            "max_ratio": max(available_ratios),
            "all_ratios": available_ratios
        }
    else:
        return {
            "min_ratio": None,
            "max_ratio": None,
            "all_ratios": []
        }

@router.get("/efficiency/machines/{machine_id}/ratio-analysis")
def get_machine_ratio_analysis(
    machine_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère l'analyse complète des ratios pour une machine
    avec des steps de 0.1 pour le graphique
    """
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Récupérer les données de marché depuis le cache
    from ..services.market_cache import MarketCacheService
    cache_service = MarketCacheService(db)
    market_data = cache_service.get_market_data()
    bitcoin_price = market_data["bitcoin_price"] if market_data["bitcoin_price"] is not None else None
    
    # Récupérer les taux d'électricité depuis la configuration
    tier1_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_rate").first()
    tier2_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier2_rate").first()
    tier1_limit_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_limit").first()
    
    electricity_tier1_rate = float(tier1_config.value) if (tier1_config and tier1_config.value) else None
    electricity_tier2_rate = float(tier2_config.value) if (tier2_config and tier2_config.value) else None
    electricity_tier1_limit = int(tier1_limit_config.value) if (tier1_limit_config and tier1_limit_config.value) else None
    
    results = []
    
    # Trouver tous les ratios disponibles
    available_ratios = get_available_ratios(machine_id, db)
    
    # Tester tous les ratios disponibles
    for ratio in available_ratios["all_ratios"]:
        try:
            # Obtenir l'efficacité pour ce ratio
            result = db.execute(text("""
                SELECT effective_hashrate, power_consumption 
                FROM get_machine_efficiency_interpolated(:machine_id, :ratio)
            """), {"machine_id": machine_id, "ratio": ratio})
            
            efficiency = result.fetchone()
            if efficiency and efficiency[0] is not None:
                hashrate = float(efficiency[0])
                power = int(efficiency[1])
                
                # Calculer les revenus basés sur les accepted shares
                daily_revenue = None
                
                # Vérifier si la machine a des accepted shares configurées
                if machine.accepted_shares_24h is not None:
                    try:
                        # Récupérer la difficulté du réseau
                        import requests
                        difficulty_response = requests.get("https://blockchain.info/q/getdifficulty", timeout=10)
                        difficulty_response.raise_for_status()
                        network_difficulty = float(difficulty_response.text)
                        
                        # Récupérer la récompense de bloc
                        block_reward_response = requests.get("https://blockchain.info/q/bcperblock", timeout=10)
                        block_reward_response.raise_for_status()
                        coinbase_reward = float(block_reward_response.text)
                        
                        # Calculer le revenu avec la formule CRC = C × S/D
                        # Répartir les shares proportionnellement au hashrate de ce ratio
                        machine_shares = float(machine.accepted_shares_24h) * (hashrate / float(machine.hashrate_nominal))
                        btc_earned_24h = (coinbase_reward * machine_shares) / network_difficulty
                        
                        if bitcoin_price is not None:
                            daily_revenue = btc_earned_24h * bitcoin_price
                    except Exception:
                        # En cas d'erreur, revenu non calculable
                        daily_revenue = None
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                if electricity_tier1_rate is None or electricity_tier2_rate is None or electricity_tier1_limit is None:
                    daily_electricity_cost = None
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue is None or daily_electricity_cost is None:
                    daily_profit = None
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                results.append({
                    "ratio": ratio,
                    "hashrate": hashrate,
                    "power": power,
                    "daily_revenue": "N/A" if daily_revenue is None else round(daily_revenue, 2),
                    "daily_cost": round(daily_electricity_cost, 2) if daily_electricity_cost is not None else None,
                    "daily_profit": "N/A" if daily_profit is None else round(daily_profit, 2),
                    "efficiency_th_per_watt": round(hashrate / power, 4) if power > 0 else 0
                })
                    
        except Exception as e:
            continue
    
    return {
        "machine_id": machine_id,
        "machine_model": machine.model,
        "bitcoin_price": bitcoin_price,
        "accepted_shares_24h": machine.accepted_shares_24h,
        "electricity_tier1_rate": electricity_tier1_rate,
        "electricity_tier2_rate": electricity_tier2_rate,
        "electricity_tier1_limit": electricity_tier1_limit,
        "results": results,
        "available_ratios": available_ratios,
        "revenue_note": "Revenus calculés avec la formule CRC = C × S/D basée sur les accepted shares" if machine.accepted_shares_24h is not None else "Revenus non calculables - configurez les accepted shares pour cette machine"
    }

@router.get("/efficiency/machines/{machine_id}/available-ratios")
def get_machine_available_ratios(machine_id: int, db: Session = Depends(get_db)):
    """
    Récupère les ratios minimum et maximum disponibles pour une machine
    """
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    available_ratios = get_available_ratios(machine_id, db)
    
    return {
        "machine_id": machine_id,
        "machine_model": machine.model,
        "available_ratios": available_ratios
    }

@router.get("/efficiency/machines/{machine_id}/optimal-efficiency")
def find_optimal_efficiency_ratio(
    machine_id: int,
    db: Session = Depends(get_db)
):
    """
    Trouve le ratio d'ajustement avec la meilleure efficacité technique (TH/s par Watt)
    en testant différents ratios de 0.5 à 1.0
    """
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Récupérer les données communes
    common_data = get_market_and_electricity_data(db)
    bitcoin_price = common_data["bitcoin_price"]
    fpps_rate = common_data["fpps_rate"]
    electricity_tier1_rate = common_data["electricity_tier1_rate"]
    electricity_tier2_rate = common_data["electricity_tier2_rate"]
    electricity_tier1_limit = common_data["electricity_tier1_limit"]
    
    optimal_ratio = None
    max_efficiency = float('-inf')
    results = []
    
    # Tester des ratios de 0.5 à 1.5 par incréments de 0.05
    for ratio in [round(x * 0.05, 2) for x in range(10, 31)]:  # 0.5 à 1.5
        try:
            # Obtenir l'efficacité pour ce ratio
            result = db.execute(text("""
                SELECT effective_hashrate, power_consumption 
                FROM get_machine_efficiency_interpolated(:machine_id, :ratio)
            """), {"machine_id": machine_id, "ratio": ratio})
            
            efficiency = result.fetchone()
            if efficiency and efficiency[0] is not None:
                hashrate = float(efficiency[0])
                power = int(efficiency[1])
                
                # Calculer l'efficacité technique (TH/s par Watt)
                efficiency_ratio = hashrate / power if power > 0 else 0
                
                # Calculer les données économiques (comme dans optimal-ratio)
                daily_revenue = None
                daily_electricity_cost = None
                daily_profit = None
                sats_per_hour = None
                
                # Calculer les revenus basés sur les accepted shares
                if machine.accepted_shares_24h is not None:
                    try:
                        # Récupérer la difficulté du réseau
                        import requests
                        difficulty_response = requests.get("https://blockchain.info/q/getdifficulty", timeout=10)
                        difficulty_response.raise_for_status()
                        network_difficulty = float(difficulty_response.text)
                        
                        # Récupérer la récompense de bloc
                        block_reward_response = requests.get("https://blockchain.info/q/bcperblock", timeout=10)
                        block_reward_response.raise_for_status()
                        coinbase_reward = float(block_reward_response.text)
                        
                        # Calculer le revenu avec la formule CRC = C × S/D
                        # Répartir les shares proportionnellement au hashrate de ce ratio
                        machine_shares = float(machine.accepted_shares_24h) * (hashrate / float(machine.hashrate_nominal))
                        btc_earned_24h = (coinbase_reward * machine_shares) / network_difficulty
                        
                        if bitcoin_price is not None:
                            daily_revenue = btc_earned_24h * bitcoin_price
                            # Calculer les sats/heure pour l'affichage
                            sats_per_hour = int((btc_earned_24h * 100000000) / 24)
                    except Exception:
                        # En cas d'erreur, revenu non calculable
                        daily_revenue = None
                        sats_per_hour = None
                else:
                    # Pas d'accepted shares => pas de revenus calculables
                    daily_revenue = None
                    sats_per_hour = None
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                if electricity_tier1_rate is None or electricity_tier2_rate is None or electricity_tier1_limit is None:
                    daily_electricity_cost = None
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue is None or daily_electricity_cost is None:
                    daily_profit = None
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                result_data = {
                    "adjustment_ratio": ratio,
                    "effective_hashrate": hashrate,
                    "power_consumption": power,
                    "efficiency_th_per_watt": round(efficiency_ratio, 6),
                    "efficiency_j_per_th": round(power / hashrate, 2) if hashrate > 0 else 0,
                    "sats_per_hour": sats_per_hour,
                    "daily_revenue": "N/A" if daily_revenue is None else round(daily_revenue, 2),
                    "daily_electricity_cost": round(daily_electricity_cost, 2) if daily_electricity_cost is not None else None,
                    "daily_profit": "N/A" if daily_profit is None else round(daily_profit, 2)
                }
                results.append(result_data)
                
                # Mettre à jour l'optimal si ce ratio a une meilleure efficacité
                if efficiency_ratio > max_efficiency:
                    max_efficiency = efficiency_ratio
                    optimal_ratio = ratio
                    
        except Exception as e:
            continue
    
    if optimal_ratio is None:
        raise HTTPException(status_code=400, detail="Impossible de calculer l'optimal")
    
    # Déterminer le message selon la disponibilité des shares
    # Vérifier si au moins un résultat a des profits calculables
    has_profitable_results = any(r["daily_profit"] != "N/A" and r["daily_profit"] is not None for r in results)
    
    if not has_profitable_results:
        message = "⚠️ Aucun profit calculable car pas d'accepted shares configurées. Configurez des shares pour voir les profits optimaux."
        shares_warning = True
    else:
        message = f"Ratio optimal trouvé: {optimal_ratio} (maximise l'efficacité TH/s par Watt)"
        shares_warning = False
    
    return {
        "machine_id": machine_id,
        "optimal_ratio": optimal_ratio,
        "max_efficiency_th_per_watt": round(max_efficiency, 6),
        "all_results": results,
        "message": message,
        "shares_warning": shares_warning
    }

@router.get("/efficiency/machines/{machine_id}/optimal-sats")
def find_optimal_sats_ratio(
    machine_id: int,
    db: Session = Depends(get_db)
):
    """
    Trouve le ratio d'ajustement qui maximise les sats par jour
    en testant différents ratios de 0.5 à 1.0
    """
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Récupérer les données communes
    common_data = get_market_and_electricity_data(db)
    bitcoin_price = common_data["bitcoin_price"]
    fpps_rate = common_data["fpps_rate"]
    electricity_tier1_rate = common_data["electricity_tier1_rate"]
    electricity_tier2_rate = common_data["electricity_tier2_rate"]
    electricity_tier1_limit = common_data["electricity_tier1_limit"]
    
    optimal_ratio = None
    max_sats_per_hour = float('-inf')
    results = []
    
    # Tester des ratios de 0.5 à 1.5 par incréments de 0.05
    for ratio in [round(x * 0.05, 2) for x in range(10, 31)]:  # 0.5 à 1.5
        try:
            # Obtenir l'efficacité pour ce ratio
            result = db.execute(text("""
                SELECT effective_hashrate, power_consumption 
                FROM get_machine_efficiency_interpolated(:machine_id, :ratio)
            """), {"machine_id": machine_id, "ratio": ratio})
            
            efficiency = result.fetchone()
            if efficiency and efficiency[0] is not None:
                hashrate = float(efficiency[0])
                power = int(efficiency[1])
                
                # Calculer l'efficacité technique (TH/s par Watt)
                efficiency_ratio = hashrate / power if power > 0 else 0
                
                # Calculer les sats/heure (priorité dans ce mode)
                sats_per_hour = None
                daily_revenue = None
                daily_electricity_cost = None
                daily_profit = None
                
                # Calculer les revenus basés sur les accepted shares
                if machine.accepted_shares_24h is not None:
                    try:
                        # Récupérer la difficulté du réseau
                        import requests
                        difficulty_response = requests.get("https://blockchain.info/q/getdifficulty", timeout=10)
                        difficulty_response.raise_for_status()
                        network_difficulty = float(difficulty_response.text)
                        
                        # Récupérer la récompense de bloc
                        block_reward_response = requests.get("https://blockchain.info/q/bcperblock", timeout=10)
                        block_reward_response.raise_for_status()
                        coinbase_reward = float(block_reward_response.text)
                        
                        # Calculer le revenu avec la formule CRC = C × S/D
                        # Répartir les shares proportionnellement au hashrate de ce ratio
                        machine_shares = float(machine.accepted_shares_24h) * (hashrate / float(machine.hashrate_nominal))
                        btc_earned_24h = (coinbase_reward * machine_shares) / network_difficulty
                        
                        if bitcoin_price is not None:
                            daily_revenue = btc_earned_24h * bitcoin_price
                            # Calculer les sats/heure pour l'affichage
                            sats_per_hour = int((btc_earned_24h * 100000000) / 24)
                    except Exception:
                        # En cas d'erreur, revenu non calculable
                        daily_revenue = None
                        sats_per_hour = None
                else:
                    # Pas d'accepted shares => pas de revenus calculables
                    daily_revenue = None
                    sats_per_hour = None
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                if electricity_tier1_rate is None or electricity_tier2_rate is None or electricity_tier1_limit is None:
                    daily_electricity_cost = None
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue is None or daily_electricity_cost is None:
                    daily_profit = None
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                result_data = {
                    "adjustment_ratio": ratio,
                    "effective_hashrate": hashrate,
                    "power_consumption": power,
                    "efficiency_th_per_watt": round(efficiency_ratio, 6),
                    "efficiency_j_per_th": round(power / hashrate, 2) if hashrate > 0 else 0,
                    "sats_per_hour": sats_per_hour,
                    "daily_revenue": "N/A" if daily_revenue is None else round(daily_revenue, 2),
                    "daily_electricity_cost": round(daily_electricity_cost, 2) if daily_electricity_cost is not None else None,
                    "daily_profit": "N/A" if daily_profit is None else round(daily_profit, 2)
                }
                results.append(result_data)
                
                # Trouver le ratio qui maximise les sats/heure
                if sats_per_hour is not None and sats_per_hour > max_sats_per_hour:
                    max_sats_per_hour = sats_per_hour
                    optimal_ratio = ratio
                
        except Exception as e:
            continue
    
    # Si aucun ratio optimal basé sur les sats n'a été trouvé (pas de shares configurées)
    # utiliser le premier ratio valide avec des données "N/A"
    if optimal_ratio is None and results:
        optimal_ratio = results[0]["adjustment_ratio"]
    
    if optimal_ratio is None:
        raise HTTPException(status_code=400, detail="Aucun ratio valide trouvé")
    
    # Déterminer le message selon la disponibilité des shares
    if max_sats_per_hour == float('-inf'):
        message = "⚠️ Aucun profit calculable car pas d'accepted shares configurées. Configurez des shares pour voir les profits optimaux."
        shares_warning = True
    else:
        message = f"Ratio optimal trouvé: {optimal_ratio} (maximise les sats/heure)"
        shares_warning = False
    
    return {
        "optimal_ratio": optimal_ratio,
        "all_results": results,
        "message": message,
        "shares_warning": shares_warning
    } 