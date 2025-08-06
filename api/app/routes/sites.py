from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from ..database import get_db
from ..models import models
from ..models.schemas import MiningSite, MiningSiteCreate, MiningSiteUpdate, SiteMachineInstance, SiteMachineInstanceCreate, SiteMachineInstanceUpdate
from ..routes.efficiency import find_optimal_adjustment_ratio

router = APIRouter()

@router.get("/sites", response_model=List[MiningSite])
async def get_sites(db: Session = Depends(get_db)):
    """Récupérer tous les sites de minage"""
    sites = db.query(models.MiningSite).all()
    return sites

@router.get("/sites/{site_id}", response_model=MiningSite)
async def get_site(site_id: int, db: Session = Depends(get_db)):
    """Récupérer un site spécifique"""
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return site

@router.post("/sites", response_model=MiningSite)
async def create_site(site: MiningSiteCreate, db: Session = Depends(get_db)):
    """Créer un nouveau site de minage"""
    db_site = models.MiningSite(**site.dict())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

@router.put("/sites/{site_id}", response_model=MiningSite)
async def update_site(site_id: int, site_update: MiningSiteUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un site de minage"""
    db_site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    update_data = site_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_site, field, value)
    
    db.commit()
    db.refresh(db_site)
    return db_site

@router.delete("/sites/{site_id}")
async def delete_site(site_id: int, db: Session = Depends(get_db)):
    """Supprimer un site de minage"""
    db_site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    try:
        db.delete(db_site)
        db.commit()
        return {"message": "Site supprimé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression du site: {str(e)}")

# Routes pour les instances de machines par site
@router.get("/site-machines", response_model=List[SiteMachineInstance])
async def get_all_site_machines(db: Session = Depends(get_db)):
    """Récupérer toutes les instances de machines par site"""
    site_machines = db.query(models.SiteMachineInstance).all()
    return site_machines

@router.get("/sites/{site_id}/machines", response_model=List[SiteMachineInstance])
async def get_site_machines(site_id: int, db: Session = Depends(get_db)):
    """Récupérer toutes les instances de machines d'un site"""
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    site_machines = db.query(models.SiteMachineInstance).filter(models.SiteMachineInstance.site_id == site_id).all()
    return site_machines

@router.post("/sites/{site_id}/machines", response_model=SiteMachineInstance)
async def add_machine_to_site(site_id: int, site_machine: SiteMachineInstanceCreate, db: Session = Depends(get_db)):
    """Ajouter une instance de machine à un site"""
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Vérifier que le template existe
    template = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == site_machine.template_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Vérifier si cette instance est déjà sur ce site
    existing = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id,
        models.SiteMachineInstance.template_id == site_machine.template_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Cette instance est déjà sur ce site")
    
    db_site_machine = models.SiteMachineInstance(**site_machine.dict())
    db_site_machine.site_id = site_id
    db.add(db_site_machine)
    db.commit()
    db.refresh(db_site_machine)
    return db_site_machine

@router.put("/sites/{site_id}/machines/{machine_id}", response_model=SiteMachineInstance)
async def update_site_machine(
    site_id: int, 
    machine_id: int, 
    site_machine_update: SiteMachineInstanceUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour une instance de machine sur un site"""
    db_site_machine = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id,
        models.SiteMachineInstance.template_id == machine_id
    ).first()
    
    if not db_site_machine:
        raise HTTPException(status_code=404, detail="Instance non trouvée sur ce site")
    
    update_data = site_machine_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_site_machine, field, value)
    
    db.commit()
    db.refresh(db_site_machine)
    return db_site_machine

@router.delete("/sites/{site_id}/machines/{machine_id}")
async def remove_machine_from_site(site_id: int, machine_id: int, db: Session = Depends(get_db)):
    """Retirer une instance de machine d'un site"""
    db_site_machine = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id,
        models.SiteMachineInstance.template_id == machine_id
    ).first()
    
    if not db_site_machine:
        raise HTTPException(status_code=404, detail="Instance non trouvée sur ce site")
    
    db.delete(db_site_machine)
    db.commit()
    return {"message": "Instance retirée du site avec succès"}

def get_machine_optimal_data(template_id: int, db: Session):
    """
    Récupère les données optimales d'une machine (hashrate et puissance optimaux)
    """
    try:
        # Récupérer les données de marché pour le calcul
        from ..services.market_cache import MarketCacheService
        cache_service = MarketCacheService(db)
        market_data = cache_service.get_market_data()
        bitcoin_price = market_data["bitcoin_price"] or -1
        fpps_rate = market_data["fpps_rate"]
        
        # Récupérer les taux d'électricité
        tier1_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_rate").first()
        tier2_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier2_rate").first()
        
        electricity_tier1_rate = float(tier1_config.value) if tier1_config else 0
        electricity_tier2_rate = float(tier2_config.value) if tier2_config else 0
        
        # Calculer l'optimal avec les données actuelles
        optimal_result = find_optimal_adjustment_ratio(
            machine_id=template_id,
            db=db
        )
        
        if optimal_result and optimal_result.get('optimal_ratio') is not None:
            # Récupérer le template pour les données nominales
            template = db.query(models.MachineTemplate).filter(
                models.MachineTemplate.id == template_id,
                models.MachineTemplate.is_active == True
            ).first()
            
            if template:
                # Calculer les données optimales basées sur le ratio optimal
                optimal_ratio = optimal_result['optimal_ratio']
                hashrate = float(template.hashrate_nominal) * optimal_ratio
                power = float(template.power_nominal) * optimal_ratio
                
                return {
                    'hashrate': hashrate,
                    'power': power,
                    'optimal_ratio': optimal_ratio
                }
        
        # Fallback aux données nominales si pas d'optimal trouvé
        template = db.query(models.MachineTemplate).filter(
            models.MachineTemplate.id == template_id,
            models.MachineTemplate.is_active == True
        ).first()
        
        if template:
            return {
                'hashrate': float(template.hashrate_nominal),
                'power': float(template.power_nominal),
                'optimal_ratio': None
            }
        
        return {'hashrate': 0, 'power': 0, 'optimal_ratio': None}
        
    except Exception as e:
        print(f"Erreur lors du calcul des données optimales: {str(e)}")
        # Fallback aux données nominales
        template = db.query(models.MachineTemplate).filter(
            models.MachineTemplate.id == template_id,
            models.MachineTemplate.is_active == True
        ).first()
        
        if template:
            return {
                'hashrate': float(template.hashrate_nominal),
                'power': float(template.power_nominal),
                'optimal_ratio': None
            }
        
        return {'hashrate': 0, 'power': 0, 'optimal_ratio': None}

def calculate_multi_machine_optimal_ratios(site_id: int, db: Session):
    """
    Calcule les ratios optimaux pour toutes les machines d'un site
    en utilisant l'approche séquentielle (tri par efficacité + optimisation individuelle)
    """
    try:
        # Récupérer le site
        site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
        if not site:
            return None
        
        # Récupérer les instances de machines du site
        instances = db.query(models.SiteMachineInstance).filter(
            models.SiteMachineInstance.site_id == site_id
        ).all()
        
        if not instances:
            return {
                "site_name": site.name,
                "machines": [],
                "total_hashrate": 0,
                "total_power": 0,
                "total_revenue": 0,
                "total_cost": 0,
                "total_profit": 0
            }
        
        # Récupérer les données de marché
        from ..services.market_cache import MarketCacheService
        cache_service = MarketCacheService(db)
        market_data = cache_service.get_market_data()
        bitcoin_price = market_data["bitcoin_price"] or -1
        fpps_rate = market_data["fpps_rate"]
        
        # Récupérer les taux d'électricité
        tier1_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_rate").first()
        tier2_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier2_rate").first()
        tier1_limit_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_limit").first()
        
        electricity_tier1_rate = float(tier1_config.value) if tier1_config else 0
        electricity_tier2_rate = float(tier2_config.value) if tier2_config else 0
        electricity_tier1_limit = int(tier1_limit_config.value) if tier1_limit_config else 0
        
        # Étape 1: Préparer les machines avec leurs données nominales
        machines_data = []
        for instance in instances:
            template = db.query(models.MachineTemplate).filter(
                models.MachineTemplate.id == instance.template_id,
                models.MachineTemplate.is_active == True
            ).first()
            
            if not template:
                continue
            
            # Calculer l'efficacité nominale (TH/s par Watt)
            efficiency = float(template.hashrate_nominal) / float(template.power_nominal) if template.power_nominal > 0 else 0
            
            for i in range(instance.quantity):
                machine_name = f"{instance.custom_name or template.model} #{i+1}"
                
                machines_data.append({
                    "instance_id": instance.id,
                    "template_id": template.id,
                    "name": machine_name,
                    "template_model": template.model,
                    "nominal_hashrate": float(template.hashrate_nominal),
                    "nominal_power": float(template.power_nominal),
                    "efficiency": efficiency,
                    "optimal_ratio": None,  # Pas de valeur par défaut
                    "optimal_hashrate": float(template.hashrate_nominal),
                    "optimal_power": float(template.power_nominal),
                    "daily_revenue": 0,
                    "daily_cost": 0,
                    "daily_profit": 0
                })
        
        # Étape 2: Trier par efficacité (plus efficaces en premier)
        machines_data.sort(key=lambda x: x["efficiency"], reverse=True)
        
        # Étape 3: Optimiser chaque machine séquentiellement
        remaining_tier1_kwh = electricity_tier1_limit
        total_hashrate = 0
        total_power = 0
        total_revenue = 0
        total_cost = 0
        
        for machine in machines_data:
            # Optimiser cette machine individuellement
            optimal_result = find_optimal_adjustment_ratio(
                machine_id=machine["template_id"],
                db=db
            )
            
            if optimal_result and optimal_result.get('optimal_ratio') is not None:
                optimal_ratio = optimal_result['optimal_ratio']
            else:
                optimal_ratio = None
            
            # Appliquer le ratio optimal
            machine["optimal_ratio"] = optimal_ratio
            machine["optimal_hashrate"] = machine["nominal_hashrate"] * optimal_ratio
            machine["optimal_power"] = machine["nominal_power"] * optimal_ratio
            
            # Calculer les revenus
            daily_revenue = 0
            if fpps_rate and bitcoin_price != -1:
                fpps_sats_per_day = int(float(fpps_rate) * 100000000)
                sats_per_hour = int(machine["optimal_hashrate"] * fpps_sats_per_day / 24)
                hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                daily_revenue = hourly_revenue_cad * 24
            
            machine["daily_revenue"] = daily_revenue
            
            # Calculer les coûts avec paliers
            daily_power_kwh = (machine["optimal_power"] * 24) / 1000
            
            if remaining_tier1_kwh > 0:
                # Utiliser le premier palier
                if daily_power_kwh <= remaining_tier1_kwh:
                    machine_cost = daily_power_kwh * electricity_tier1_rate
                    remaining_tier1_kwh -= daily_power_kwh
                else:
                    # Partie premier palier
                    tier1_cost = remaining_tier1_kwh * electricity_tier1_rate
                    # Partie deuxième palier
                    tier2_kwh = daily_power_kwh - remaining_tier1_kwh
                    tier2_cost = tier2_kwh * electricity_tier2_rate
                    machine_cost = tier1_cost + tier2_cost
                    remaining_tier1_kwh = 0
            else:
                # Utiliser seulement le deuxième palier
                machine_cost = daily_power_kwh * electricity_tier2_rate
            
            machine["daily_cost"] = machine_cost
            machine["daily_profit"] = daily_revenue - machine_cost
            
            # Ajouter aux totaux
            total_hashrate += machine["optimal_hashrate"]
            total_power += machine["optimal_power"]
            total_revenue += daily_revenue
            total_cost += machine_cost
        
        total_profit = total_revenue - total_cost
        
        return {
            "site_name": site.name,
            "electricity_tier1_rate": electricity_tier1_rate,
            "electricity_tier2_rate": electricity_tier2_rate,
            "electricity_tier1_limit": electricity_tier1_limit,
            "machines": machines_data,
            "total_hashrate": total_hashrate,
            "total_power": total_power,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit
        }
        
    except Exception as e:
        print(f"Erreur lors du calcul multi-machines: {str(e)}")
        return None

# Route pour calculer le profit d'un site
@router.get("/sites/{site_id}/profit-calculation")
async def calculate_site_profit(
    site_id: int,
    bitcoin_price: float = 50000,
    fpps_sats: int = 48,
    db: Session = Depends(get_db)
):
    """Calculer le profit total d'un site avec toutes ses machines"""
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Récupérer toutes les instances de machines du site
    site_machines = db.query(models.SiteMachineInstance).filter(models.SiteMachineInstance.site_id == site_id).all()
    
    total_daily_profit = 0
    total_daily_revenue = 0
    total_daily_cost = 0
    machines_results = []
    
    for site_machine in site_machines:
        template = db.query(models.MachineTemplate).filter(
            models.MachineTemplate.id == site_machine.template_id,
            models.MachineTemplate.is_active == True
        ).first()
        if template:
            # Calculer le profit pour cette instance (simplifié pour l'instant)
            # TODO: Utiliser les vraies fonctions SQL avec paliers
            daily_revenue = float(template.hashrate_nominal) * (fpps_sats / 100000000) * bitcoin_price
            daily_cost = (template.power_nominal * 24 / 1000) * 0.08  # Taux simplifié
            daily_profit = daily_revenue - daily_cost
            
            total_daily_revenue += daily_revenue * site_machine.quantity
            total_daily_cost += daily_cost * site_machine.quantity
            total_daily_profit += daily_profit * site_machine.quantity
            
            machines_results.append({
                "template_id": template.id,
                "template_model": template.model,
                "quantity": site_machine.quantity,
                "custom_name": site_machine.custom_name,
                "daily_revenue": round(daily_revenue, 2),
                "daily_cost": round(daily_cost, 2),
                "daily_profit": round(daily_profit, 2)
            })
    
    return {
        "site_id": site_id,
        "site_name": site.name,
        "total_daily_revenue": round(total_daily_revenue, 2),
        "total_daily_cost": round(total_daily_cost, 2),
        "total_daily_profit": round(total_daily_profit, 2),
        "machines": machines_results
    } 

@router.get("/sites/{site_id}/summary")
async def get_site_summary(site_id: int, db: Session = Depends(get_db)):
    """
    Récupère la synthèse d'un site avec calcul des paliers d'électricité
    """
    try:
        # Récupérer le site
        site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site non trouvé")
        
        # Récupérer les instances de machines du site
        instances = db.query(models.SiteMachineInstance).filter(
            models.SiteMachineInstance.site_id == site_id
        ).all()
        
        if not instances:
            return {
                "site_name": site.name,
                "machines": [],
                "total_hashrate": 0,
                "total_power": 0,
                "total_revenue": 0,
                "total_cost": 0,
                "total_profit": 0
            }
        
        # Récupérer les données de marché
        from ..services.market_cache import MarketCacheService
        cache_service = MarketCacheService(db)
        market_data = cache_service.get_market_data()
        bitcoin_price = market_data["bitcoin_price"] or -1
        fpps_rate = market_data["fpps_rate"]
        
        # Récupérer les taux d'électricité
        tier1_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_rate").first()
        tier2_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier2_rate").first()
        tier1_limit_config = db.query(models.AppConfig).filter(models.AppConfig.key == "electricity_tier1_limit").first()
        
        electricity_tier1_rate = float(tier1_config.value) if tier1_config else 0
        electricity_tier2_rate = float(tier2_config.value) if tier2_config else 0
        electricity_tier1_limit = int(tier1_limit_config.value) if tier1_limit_config else 0
        
        # Calculer les données pour chaque machine
        machines_data = []
        total_hashrate = 0
        total_power = 0
        total_revenue = 0
        
        for instance in instances:
            # Récupérer le template
            template = db.query(models.MachineTemplate).filter(
                models.MachineTemplate.id == instance.template_id,
                models.MachineTemplate.is_active == True
            ).first()
            
            if not template:
                continue
            
            # Récupérer les données optimales de la machine
            optimal_data = get_machine_optimal_data(template.id, db)
            hashrate = optimal_data.get('hashrate', template.hashrate_nominal)
            power = optimal_data.get('power', template.power_nominal)
            optimal_ratio = optimal_data.get('optimal_ratio', None)
            
            # Calculer les revenus
            daily_revenue = 0
            if fpps_rate and bitcoin_price != -1:
                fpps_sats_per_day = int(float(fpps_rate) * 100000000)
                sats_per_hour = int(hashrate * fpps_sats_per_day / 24)
                hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                daily_revenue = hourly_revenue_cad * 24
            
            # Créer une ligne pour chaque machine individuelle
            for i in range(instance.quantity):
                machine_name = f"{instance.custom_name or template.model} #{i+1}"
                
                machines_data.append({
                    "instance_id": instance.id,
                    "template_id": template.id,
                    "name": machine_name,
                    "template_model": template.model,
                    "hashrate": hashrate,
                    "power": power,
                    "daily_revenue": daily_revenue,
                    "efficiency_th_per_watt": hashrate / power if power > 0 else 0,
                    "optimal_ratio": optimal_ratio
                })
                
                total_hashrate += hashrate
                total_power += power
                total_revenue += daily_revenue
        
        # Trier par efficacité (TH/s par Watt) - les plus efficaces en premier
        machines_data.sort(key=lambda x: x["efficiency_th_per_watt"], reverse=True)
        
        # Calculer les coûts d'électricité avec paliers
        total_cost = 0
        remaining_tier1_kwh = electricity_tier1_limit
        
        for machine in machines_data:
            daily_power_kwh = (machine["power"] * 24) / 1000
            
            if remaining_tier1_kwh > 0:
                # Utiliser le premier palier
                if daily_power_kwh <= remaining_tier1_kwh:
                    machine_cost = daily_power_kwh * electricity_tier1_rate
                    remaining_tier1_kwh -= daily_power_kwh
                else:
                    # Partie premier palier
                    tier1_cost = remaining_tier1_kwh * electricity_tier1_rate
                    # Partie deuxième palier
                    tier2_kwh = daily_power_kwh - remaining_tier1_kwh
                    tier2_cost = tier2_kwh * electricity_tier2_rate
                    machine_cost = tier1_cost + tier2_cost
                    remaining_tier1_kwh = 0
            else:
                # Utiliser seulement le deuxième palier
                machine_cost = daily_power_kwh * electricity_tier2_rate
            
            machine["daily_cost"] = machine_cost
            machine["daily_profit"] = machine["daily_revenue"] - machine_cost
            total_cost += machine_cost
        
        total_profit = total_revenue - total_cost
        
        return {
            "site_name": site.name,
            "electricity_tier1_rate": electricity_tier1_rate,
            "electricity_tier2_rate": electricity_tier2_rate,
            "electricity_tier1_limit": electricity_tier1_limit,
            "machines": machines_data,
            "total_hashrate": total_hashrate,
            "total_power": total_power,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit
                } 
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de la synthèse: {str(e)}")

@router.get("/sites/{site_id}/multi-optimal")
async def get_site_multi_optimal_ratios(site_id: int, db: Session = Depends(get_db)):
    """
    Calcule les ratios optimaux pour toutes les machines d'un site
    en utilisant l'approche séquentielle (tri par efficacité + optimisation individuelle)
    """
    try:
        result = calculate_multi_machine_optimal_ratios(site_id, db)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Site non trouvé ou erreur de calcul")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul multi-optimal: {str(e)}") 