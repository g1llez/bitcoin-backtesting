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
    bitcoin_price = market_data["bitcoin_price"] or -1
    fpps_rate = market_data["fpps_rate"]
    
    # Récupérer les taux d'électricité depuis la configuration
    tier1_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_rate").first()
    tier2_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier2_rate").first()
    tier1_limit_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_limit").first()
    
    electricity_tier1_rate = float(tier1_config.value) if tier1_config else -1
    electricity_tier2_rate = float(tier2_config.value) if tier2_config else -1
    electricity_tier1_limit = int(tier1_limit_config.value) if tier1_limit_config else -1
    
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
                
                # Calculer les revenus avec les données du cache
                daily_revenue = -1
                sats_per_hour = -1
                
                # Utiliser les données FPPS du cache (déjà récupérées)
                if fpps_rate and fpps_rate != -1:
                    # FPPS est en BTC/jour par TH/s, convertir en sats/jour par TH/s
                    fpps_sats_per_day = int(round(float(fpps_rate) * 100000000))
                    
                    # Calculer les sats/heure : hashrate (TH/s) × FPPS (sats/jour/TH/s) / 24
                    sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                    
                    # Convertir en CAD : sats/heure × prix Bitcoin (CAD) / 100000000
                    if bitcoin_price != -1:
                        hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                        daily_revenue = hourly_revenue_cad * 24
                    
                    # Stocker les sats/heure pour l'affichage
                    sats_per_hour = sats_per_hour  # Déjà calculé ci-dessus
                else:
                    # Si pas de données FPPS, essayer de récupérer depuis l'API Braiins directement
                    try:
                        import requests
                        
                        # Récupérer le token depuis la configuration
                        braiins_token_config = db.query(models.AppConfig).filter(models.AppConfig.key == "braiins_token").first()
                        
                        if braiins_token_config and braiins_token_config.value:
                            # Appel avec le token
                            fpps_response = requests.get(
                                "https://pool.braiins.com/stats/json/btc",
                                headers={"Pool-Auth-Token": braiins_token_config.value},
                                timeout=3
                            )
                        else:
                            # Appel sans token (données publiques limitées)
                            fpps_response = requests.get("https://pool.braiins.com/stats/json/btc", timeout=3)
                        
                        if fpps_response.status_code == 200:
                            fpps_data = fpps_response.json()
                            fpps_rate = fpps_data.get('btc', {}).get('fpps_rate')
                            
                            if fpps_rate and fpps_rate != -1:
                                # FPPS est en BTC/jour par TH/s, convertir en sats/jour par TH/s
                                fpps_sats_per_day = int(round(float(fpps_rate) * 100000000))
                                
                                # Calculer les sats/heure : hashrate (TH/s) × FPPS (sats/jour/TH/s) / 24
                                sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                                
                                # Convertir en CAD : sats/heure × prix Bitcoin (CAD) / 100000000
                                if bitcoin_price != -1:
                                    hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                                    daily_revenue = hourly_revenue_cad * 24
                                
                                # Stocker les sats/heure pour l'affichage
                                sats_per_hour = sats_per_hour  # Déjà calculé ci-dessus
                    except Exception as e:
                        # En cas d'erreur, garder les valeurs par défaut
                        daily_revenue = -1
                        sats_per_hour = -1
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                # Calculer le coût avec les paliers
                if electricity_tier1_rate == -1 or electricity_tier2_rate == -1 or electricity_tier1_limit == -1:
                    daily_electricity_cost = -1
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue == -1 or daily_electricity_cost == -1:
                    daily_profit = -1
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
                    "sats_per_hour": sats_per_hour if 'sats_per_hour' in locals() else -1,
                    "daily_revenue": round(daily_revenue, 2),
                    "daily_electricity_cost": round(daily_electricity_cost, 2),
                    "daily_profit": round(daily_profit, 2)
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
        global_max_profit = best_hashrate_result.get('daily_profit', -1)
    
    # Si toujours aucun résultat, utiliser le ratio par défaut
    if global_optimal_ratio is None:
        global_optimal_ratio = 0.85  # Ratio par défaut
        global_max_profit = -1
    
    
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
    optimal_ratio = global_optimal_ratio  # Valeur par défaut
    max_profit = global_max_profit  # Valeur par défaut
    
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
                
                # Calculer les revenus avec les données du cache
                daily_revenue = -1
                sats_per_hour = -1
                
                # Utiliser les données FPPS du cache (déjà récupérées)
                if fpps_rate and fpps_rate != -1:
                    # FPPS est en BTC/jour par TH/s, convertir en sats/jour par TH/s
                    fpps_sats_per_day = int(round(float(fpps_rate) * 100000000))
                    
                    # Calculer les sats/heure : hashrate (TH/s) × FPPS (sats/jour/TH/s) / 24
                    sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                    
                    # Convertir en CAD : sats/heure × prix Bitcoin (CAD) / 100000000
                    if bitcoin_price != -1:
                        hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                        daily_revenue = hourly_revenue_cad * 24
                    
                    # Stocker les sats/heure pour l'affichage
                    sats_per_hour = sats_per_hour  # Déjà calculé ci-dessus
                else:
                    # Si pas de données FPPS, essayer de récupérer depuis l'API Braiins directement
                    try:
                        import requests
                        
                        # Récupérer le token depuis la configuration
                        braiins_token_config = db.query(models.AppConfig).filter(models.AppConfig.key == "braiins_token").first()
                        
                        if braiins_token_config and braiins_token_config.value:
                            # Appel avec le token
                            fpps_response = requests.get(
                                "https://pool.braiins.com/stats/json/btc",
                                headers={"Pool-Auth-Token": braiins_token_config.value},
                                timeout=3
                            )
                        else:
                            # Appel sans token (données publiques limitées)
                            fpps_response = requests.get("https://pool.braiins.com/stats/json/btc", timeout=3)
                        
                        if fpps_response.status_code == 200:
                            fpps_data = fpps_response.json()
                            fpps_rate = fpps_data.get('btc', {}).get('fpps_rate')
                            
                            if fpps_rate and fpps_rate != -1:
                                # FPPS est en BTC/jour par TH/s, convertir en sats/jour par TH/s
                                fpps_sats_per_day = int(round(float(fpps_rate) * 100000000))
                                
                                # Calculer les sats/heure : hashrate (TH/s) × FPPS (sats/jour/TH/s) / 24
                                sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                                
                                # Convertir en CAD : sats/heure × prix Bitcoin (CAD) / 100000000
                                if bitcoin_price != -1:
                                    hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                                    daily_revenue = hourly_revenue_cad * 24
                                
                                # Stocker les sats/heure pour l'affichage
                                sats_per_hour = sats_per_hour  # Déjà calculé ci-dessus
                    except Exception as e:
                        # En cas d'erreur, garder les valeurs par défaut
                        daily_revenue = -1
                        sats_per_hour = -1
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                # Calculer le coût avec les paliers
                if electricity_tier1_rate == -1 or electricity_tier2_rate == -1 or electricity_tier1_limit == -1:
                    daily_electricity_cost = -1
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue == -1 or daily_electricity_cost == -1:
                    daily_profit = -1
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
                    "sats_per_hour": sats_per_hour if 'sats_per_hour' in locals() else -1,
                    "daily_revenue": round(daily_revenue, 2),
                    "daily_electricity_cost": round(daily_electricity_cost, 2),
                    "daily_profit": round(daily_profit, 2)
                }
                results.append(result_data)
                
                # Mettre à jour l'optimal si ce ratio est plus profitable
                if daily_profit > max_profit:
                    max_profit = daily_profit
                    optimal_ratio = ratio
                    
        except Exception as e:
            continue
    
    
    return {
        "machine_id": machine_id,
        "optimal_ratio": optimal_ratio,
        "max_daily_profit": round(max_profit, 2) if max_profit != -1 else -1,
        "all_results": results
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
    bitcoin_price = market_data["bitcoin_price"] or -1
    
    # Récupérer les taux d'électricité depuis la configuration
    tier1_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_rate").first()
    tier2_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier2_rate").first()
    tier1_limit_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_limit").first()
    
    electricity_tier1_rate = float(tier1_config.value) if tier1_config else -1
    electricity_tier2_rate = float(tier2_config.value) if tier2_config else -1
    electricity_tier1_limit = int(tier1_limit_config.value) if tier1_limit_config else -1
    
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
                
                # Calculer les revenus
                daily_revenue = -1
                if market_data["fpps_rate"] and market_data["fpps_rate"] != -1:
                    fpps_sats_per_day = int(float(market_data["fpps_rate"]) * 100000000)
                    sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                    
                    if bitcoin_price != -1:
                        hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                        daily_revenue = hourly_revenue_cad * 24
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                if electricity_tier1_rate == -1 or electricity_tier2_rate == -1 or electricity_tier1_limit == -1:
                    daily_electricity_cost = -1
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue == -1 or daily_electricity_cost == -1:
                    daily_profit = -1
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                results.append({
                    "ratio": ratio,
                    "hashrate": hashrate,
                    "power": power,
                    "daily_revenue": round(daily_revenue, 2),
                    "daily_cost": round(daily_electricity_cost, 2),
                    "daily_profit": round(daily_profit, 2),
                    "efficiency_th_per_watt": round(hashrate / power, 4) if power > 0 else 0
                })
                    
        except Exception as e:
            continue
    
    return {
        "machine_id": machine_id,
        "machine_model": machine.model,
        "bitcoin_price": bitcoin_price,
        "fpps_rate": market_data["fpps_rate"],
        "electricity_tier1_rate": electricity_tier1_rate,
        "electricity_tier2_rate": electricity_tier2_rate,
        "electricity_tier1_limit": electricity_tier1_limit,
        "results": results,
        "available_ratios": available_ratios
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
                daily_revenue = -1
                daily_electricity_cost = -1
                daily_profit = -1
                sats_per_hour = -1
                
                # Calculer les revenus avec FPPS
                if fpps_rate and fpps_rate != -1:
                    # FPPS est en BTC/jour par TH/s, convertir en sats/jour par TH/s
                    fpps_sats_per_day = int(round(float(fpps_rate) * 100000000))
                    
                    # Calculer les sats/heure : hashrate (TH/s) × FPPS (sats/jour/TH/s) / 24
                    sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                    
                    # Convertir en CAD : sats/heure × prix Bitcoin (CAD) / 100000000
                    if bitcoin_price != -1:
                        hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                        daily_revenue = hourly_revenue_cad * 24
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                if electricity_tier1_rate == -1 or electricity_tier2_rate == -1 or electricity_tier1_limit == -1:
                    daily_electricity_cost = -1
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue == -1 or daily_electricity_cost == -1:
                    daily_profit = -1
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                result_data = {
                    "adjustment_ratio": ratio,
                    "effective_hashrate": hashrate,
                    "power_consumption": power,
                    "efficiency_th_per_watt": round(efficiency_ratio, 6),
                    "efficiency_j_per_th": round(power / hashrate, 2) if hashrate > 0 else 0,
                    "sats_per_hour": sats_per_hour,
                    "daily_revenue": round(daily_revenue, 2),
                    "daily_electricity_cost": round(daily_electricity_cost, 2),
                    "daily_profit": round(daily_profit, 2)
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
    
    return {
        "machine_id": machine_id,
        "optimal_ratio": optimal_ratio,
        "max_efficiency_th_per_watt": round(max_efficiency, 6),
        "all_results": results
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
                sats_per_hour = -1
                daily_revenue = -1
                daily_electricity_cost = -1
                daily_profit = -1
                
                # Calculer les revenus avec FPPS
                if fpps_rate and fpps_rate != -1:
                    # FPPS est en BTC/jour par TH/s, convertir en sats/jour par TH/s
                    fpps_sats_per_day = int(round(float(fpps_rate) * 100000000))
                    
                    # Calculer les sats/heure : hashrate (TH/s) × FPPS (sats/jour/TH/s) / 24
                    sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                    
                    # Convertir en CAD : sats/heure × prix Bitcoin (CAD) / 100000000
                    if bitcoin_price != -1:
                        hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                        daily_revenue = hourly_revenue_cad * 24
                
                # Calculer les coûts d'électricité avec paliers
                daily_power_kwh = (power * 24) / 1000
                
                if electricity_tier1_rate == -1 or electricity_tier2_rate == -1 or electricity_tier1_limit == -1:
                    daily_electricity_cost = -1
                else:
                    if daily_power_kwh <= electricity_tier1_limit:
                        daily_electricity_cost = daily_power_kwh * electricity_tier1_rate
                    else:
                        tier1_cost = electricity_tier1_limit * electricity_tier1_rate
                        tier2_cost = (daily_power_kwh - electricity_tier1_limit) * electricity_tier2_rate
                        daily_electricity_cost = tier1_cost + tier2_cost
                
                # Calculer le profit
                if daily_revenue == -1 or daily_electricity_cost == -1:
                    daily_profit = -1
                else:
                    daily_profit = daily_revenue - daily_electricity_cost
                
                result_data = {
                    "adjustment_ratio": ratio,
                    "effective_hashrate": hashrate,
                    "power_consumption": power,
                    "efficiency_th_per_watt": round(efficiency_ratio, 6),
                    "efficiency_j_per_th": round(power / hashrate, 2) if hashrate > 0 else 0,
                    "sats_per_hour": sats_per_hour,
                    "daily_revenue": round(daily_revenue, 2),
                    "daily_electricity_cost": round(daily_electricity_cost, 2),
                    "daily_profit": round(daily_profit, 2)
                }
                results.append(result_data)
                
                # Trouver le ratio qui maximise les sats/heure
                if sats_per_hour > max_sats_per_hour:
                    max_sats_per_hour = sats_per_hour
                    optimal_ratio = ratio
                
        except Exception as e:
            continue
    
    if optimal_ratio is None:
        raise HTTPException(status_code=404, detail="Aucun ratio optimal trouvé")
    
    return {
        "optimal_ratio": optimal_ratio,
        "all_results": results
    } 