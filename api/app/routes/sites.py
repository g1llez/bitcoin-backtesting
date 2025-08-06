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
        
        # Récupérer le template pour les données nominales
        template = db.query(models.MachineTemplate).filter(
            models.MachineTemplate.id == template_id,
            models.MachineTemplate.is_active == True
        ).first()
        
        if not template:
            return {'hashrate': 0, 'power': 0, 'optimal_ratio': None, 'current_ratio': None, 'ratio_type': 'nominal'}
        
        # Calculer l'optimal avec les données actuelles
        optimal_result = find_optimal_adjustment_ratio(
            machine_id=template_id,
            db=db
        )
        
        # Déterminer le ratio actuel et le type
        current_ratio = None
        ratio_type = 'nominal'
        
        # Vérifier s'il y a un ratio manuel appliqué pour ce template dans ce site
        # Pour cela, nous devons passer le site_id à cette fonction
        # Pour l'instant, on utilise le ratio optimal comme ratio actuel
        if optimal_result and optimal_result.get('optimal_ratio') is not None:
            optimal_ratio = optimal_result['optimal_ratio']
            
            # TODO: Implémenter la logique pour récupérer le ratio manuel depuis la base
            # Pour l'instant, on utilise le ratio optimal comme ratio actuel
            current_ratio = optimal_ratio
            ratio_type = 'optimal'
            
            # Calculer les données basées sur le ratio actuel
            hashrate = float(template.hashrate_nominal) * current_ratio
            power = float(template.power_nominal) * current_ratio
            
            return {
                'hashrate': hashrate,
                'power': power,
                'optimal_ratio': optimal_ratio,
                'current_ratio': current_ratio,
                'ratio_type': ratio_type
            }
        
        # Fallback aux données nominales si pas d'optimal trouvé
        return {
            'hashrate': float(template.hashrate_nominal),
            'power': float(template.power_nominal),
            'optimal_ratio': None,
            'current_ratio': 1.0,
            'ratio_type': 'nominal'
        }
        
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
                'optimal_ratio': None,
                'current_ratio': 1.0,
                'ratio_type': 'nominal'
            }
        
        return {'hashrate': 0, 'power': 0, 'optimal_ratio': None, 'current_ratio': None, 'ratio_type': 'nominal'}

async def calculate_multi_machine_optimal_ratios(site_id: int, db: Session):
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
            # Récupérer l'instance correspondante
            instance = next((inst for inst in instances if inst.id == machine["instance_id"]), None)
            # Vérifier s'il y a un ratio manuel appliqué pour cette instance
            current_ratio = 1.0
            ratio_type = 'nominal'
            
            # Optimiser cette machine individuellement (toujours calculer l'optimal)
            optimal_result = find_optimal_adjustment_ratio(
                machine_id=machine["template_id"],
                db=db
            )
            
            if optimal_result and optimal_result.get('optimal_ratio') is not None:
                optimal_ratio = optimal_result['optimal_ratio']
            else:
                optimal_ratio = None
            
            # Déterminer le ratio actuel et le type
            if instance.optimal_ratio is not None:
                # Un ratio a été appliqué (manuel ou optimal)
                current_ratio = float(instance.optimal_ratio)
                ratio_type = instance.ratio_type or 'manual'  # Utiliser le type stocké en DB
            elif optimal_ratio is not None:
                # Utiliser le ratio optimal calculé (pas encore appliqué)
                current_ratio = optimal_ratio
                ratio_type = 'optimal'
            else:
                # Utiliser le ratio nominal (1.0)
                current_ratio = 1.0
                ratio_type = 'nominal'
            
            # Utiliser l'API d'efficacité pour obtenir les vraies courbes d'efficacité
            try:
                # Appeler l'endpoint d'efficacité pour obtenir les données réelles
                from ..routes.efficiency import get_machine_efficiency_at_ratio
                efficiency_response = await get_machine_efficiency_at_ratio(machine["template_id"], optimal_ratio, db)
                
                if efficiency_response and efficiency_response.get("effective_hashrate") and efficiency_response.get("power_consumption"):
                    real_hashrate = float(efficiency_response["effective_hashrate"])
                    real_power = int(efficiency_response["power_consumption"])
                    real_efficiency = real_hashrate / real_power if real_power > 0 else 0
                else:
                    # Pas de données d'efficacité disponibles pour ce ratio optimal
                    raise HTTPException(
                        status_code=400,
                        detail=f"Données d'efficacité non disponibles pour le ratio optimal {optimal_ratio} sur la machine {machine['template_model']}. "
                               f"Utilisez l'API /efficiency/machines/{machine['template_id']}/ratio-bounds pour voir les ratios disponibles."
                    )
            except HTTPException:
                raise
            except Exception as e:
                # En cas d'erreur technique, retourner une erreur
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de la récupération des données d'efficacité pour le ratio {optimal_ratio}: {str(e)}"
                )
            
            # Appliquer le ratio optimal
            machine["optimal_ratio"] = optimal_ratio
            machine["current_ratio"] = current_ratio
            machine["ratio_type"] = ratio_type
            machine["optimal_hashrate"] = real_hashrate
            machine["optimal_power"] = real_power
            
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
            
            # Vérifier s'il y a un ratio manuel appliqué pour cette instance
            current_ratio = 1.0
            ratio_type = 'nominal'
            
            if instance.optimal_ratio is not None:
                # Un ratio a été appliqué (manuel ou optimal)
                current_ratio = float(instance.optimal_ratio)
                ratio_type = instance.ratio_type or 'manual'  # Utiliser le type stocké en DB
                # Recalculer hashrate et power avec le ratio appliqué
                hashrate = float(template.hashrate_nominal) * current_ratio
                power = float(template.power_nominal) * current_ratio
            else:
                # Aucun ratio appliqué - utiliser le ratio nominal (1.0)
                current_ratio = 1.0
                ratio_type = 'nominal'
                hashrate = float(template.hashrate_nominal)
                power = float(template.power_nominal)
            
            # Utiliser l'API d'efficacité pour obtenir les vraies courbes d'efficacité
            try:
                # Appeler l'endpoint d'efficacité pour obtenir les données réelles
                from ..routes.efficiency import get_machine_efficiency_at_ratio
                efficiency_response = await get_machine_efficiency_at_ratio(template.id, current_ratio, db)
                
                if efficiency_response and efficiency_response.get("effective_hashrate") and efficiency_response.get("power_consumption"):
                    real_hashrate = float(efficiency_response["effective_hashrate"])
                    real_power = int(efficiency_response["power_consumption"])
                    real_efficiency = real_hashrate / real_power if real_power > 0 else 0
                    
                    # Recalculer les revenus avec le hashrate réel
                    daily_revenue = 0
                    if fpps_rate and bitcoin_price != -1:
                        fpps_sats_per_day = int(float(fpps_rate) * 100000000)
                        sats_per_hour = int(real_hashrate * fpps_sats_per_day / 24)
                        hourly_revenue_cad = sats_per_hour * bitcoin_price / 100000000
                        daily_revenue = hourly_revenue_cad * 24
                    
                    # Utiliser les données réelles
                    final_hashrate = real_hashrate
                    final_power = real_power
                    final_efficiency = real_efficiency
                else:
                    # Pas de données d'efficacité disponibles pour ce ratio
                    raise HTTPException(
                        status_code=400,
                        detail=f"Données d'efficacité non disponibles pour le ratio {current_ratio} sur la machine {template.model}. "
                               f"Utilisez l'API /efficiency/machines/{template.id}/ratio-bounds pour voir les ratios disponibles."
                    )
            except HTTPException:
                raise
            except Exception as e:
                # En cas d'erreur technique, retourner une erreur
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur lors de la récupération des données d'efficacité pour le ratio {current_ratio}: {str(e)}"
                )
            
            # Créer une ligne pour chaque machine individuelle
            for i in range(instance.quantity):
                machine_name = f"{instance.custom_name or template.model} #{i+1}"
                
                machines_data.append({
                    "instance_id": instance.id,  # ID numérique unique
                    "template_id": template.id,
                    "name": machine_name,
                    "template_model": template.model,
                    "hashrate": final_hashrate,
                    "power": final_power,
                    "daily_revenue": daily_revenue,
                    "efficiency_th_per_watt": final_efficiency,
                    "optimal_ratio": optimal_ratio,
                    "current_ratio": current_ratio,
                    "ratio_type": ratio_type
                })
                
                total_hashrate += final_hashrate
                total_power += final_power
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de la synthèse: {str(e)}")

@router.get("/sites/{site_id}/multi-optimal")
async def get_site_multi_optimal_ratios(site_id: int, db: Session = Depends(get_db)):
    """
    Calcule les ratios optimaux pour toutes les machines d'un site
    en utilise l'approche séquentielle (tri par efficacité + optimisation individuelle)
    """
    try:
        result = await calculate_multi_machine_optimal_ratios(site_id, db)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Site non trouvé ou erreur de calcul")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul multi-optimal: {str(e)}")

@router.post("/sites/{site_id}/apply-optimal-ratios")
async def apply_optimal_ratios(site_id: int, db: Session = Depends(get_db)):
    """
    Calcule ET applique automatiquement les ratios optimaux à toutes les machines d'un site
    """
    try:
        # Calculer les ratios optimaux
        result = await calculate_multi_machine_optimal_ratios(site_id, db)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Site non trouvé ou erreur de calcul")
        
        # Appliquer les ratios optimaux aux instances
        instances = db.query(models.SiteMachineInstance).filter(
            models.SiteMachineInstance.site_id == site_id
        ).all()
        
        instances_updated = 0
        total_machines = 0
        
        for instance in instances:
            # Trouver la machine correspondante dans le résultat
            machine_data = next((m for m in result["machines"] if m["instance_id"] == instance.id), None)
            
            if machine_data and machine_data["optimal_ratio"] is not None:
                # Appliquer le ratio optimal calculé
                optimal_ratio = machine_data["optimal_ratio"]
                # Si le ratio optimal est 1.0, c'est considéré comme nominal
                if optimal_ratio == 1.0:
                    instance.optimal_ratio = None
                    instance.ratio_type = 'nominal'
                else:
                    instance.optimal_ratio = optimal_ratio
                    instance.ratio_type = 'optimal'
                instances_updated += 1
                total_machines += instance.quantity
        
        db.commit()
        
        return {
            "message": f"Ratios optimaux appliqués avec succès à {total_machines} machine(s) dans {instances_updated} instance(s)",
            "instances_updated": instances_updated,
            "total_machines": total_machines,
            "site_id": site_id,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'application des ratios optimaux: {str(e)}") 

@router.post("/sites/{site_id}/apply-manual-ratio")
async def apply_manual_ratio(site_id: int, ratio_data: dict, db: Session = Depends(get_db)):
    """Appliquer un ratio manuel à toutes les machines d'un site"""
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    ratio = ratio_data.get("ratio", 1.0)
    optimization_type = ratio_data.get("optimization_type", "economic")
    
    if ratio < 0.5 or ratio > 1.5:
        raise HTTPException(status_code=400, detail="Ratio doit être entre 0.5 et 1.5")
    
    # Vérifier si le ratio est valide pour toutes les machines du site
    machines = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id
    ).all()
    
    invalid_machines = []
    for machine in machines:
        template = db.query(models.MachineTemplate).filter(
            models.MachineTemplate.id == machine.template_id,
            models.MachineTemplate.is_active == True
        ).first()
        
        if template:
            # Vérifier si le ratio est valide en testant l'API d'efficacité
            try:
                from ..routes.efficiency import get_machine_efficiency_at_ratio
                efficiency_response = await get_machine_efficiency_at_ratio(template.id, ratio, db)
                
                if not efficiency_response or not efficiency_response.get("effective_hashrate") or not efficiency_response.get("power_consumption"):
                    # Pas de données d'efficacité disponibles pour ce ratio
                    invalid_machines.append({
                        "machine": template.model,
                        "min_ratio": "voir /efficiency/machines/" + str(template.id) + "/ratio-bounds",
                        "max_ratio": "pour les limites exactes"
                    })
            except Exception:
                # En cas d'erreur, considérer comme invalide
                invalid_machines.append({
                    "machine": template.model,
                    "min_ratio": 0.5,
                    "max_ratio": 1.5
                })
    
    if invalid_machines:
        error_details = []
        for machine in invalid_machines:
            error_details.append(f"{machine['machine']}: {machine['min_ratio']}-{machine['max_ratio']}")
        
        raise HTTPException(
            status_code=400, 
            detail=f"Ratio {ratio} non valide pour certaines machines. Ratios acceptés: {', '.join(error_details)}"
        )
    
    # Récupérer toutes les machines du site
    machines = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id
    ).all()
    
    instances_updated = 0
    total_machines = 0
    
    for machine in machines:
        # Appliquer le ratio manuel
        # Si le ratio est 1.0, c'est considéré comme nominal
        if ratio == 1.0:
            machine.optimal_ratio = None
            machine.ratio_type = 'nominal'
        else:
            machine.optimal_ratio = ratio
            machine.ratio_type = 'manual'
        instances_updated += 1
        total_machines += machine.quantity
    
    db.commit()
    
    return {
        "message": f"Ratio {ratio} appliqué avec succès à {total_machines} machine(s) dans {instances_updated} instance(s)",
        "instances_updated": instances_updated,
        "total_machines": total_machines,
        "site_id": site_id,
        "ratio": ratio,
        "optimization_type": optimization_type
    }

@router.get("/sites/{site_id}/available-ratios")
async def get_site_available_ratios(site_id: int, db: Session = Depends(get_db)):
    """Récupère les ratios disponibles pour toutes les machines d'un site"""
    
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Récupérer toutes les machines du site
    machines = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id
    ).all()
    
    if not machines:
        raise HTTPException(status_code=404, detail="Aucune machine trouvée pour ce site")
    
    # Récupérer les ratios disponibles pour chaque machine
    available_ratios = {}
    common_ratios = None
    
    for machine in machines:
        template = db.query(models.MachineTemplate).filter(
            models.MachineTemplate.id == machine.template_id,
            models.MachineTemplate.is_active == True
        ).first()
        
        if template:
            try:
                # Récupérer les ratios disponibles pour cette machine
                from ..routes.efficiency import get_machine_efficiency_at_ratio
                
                # Tester différents ratios pour trouver les limites
                test_ratios = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5]
                valid_ratios = []
                
                for ratio in test_ratios:
                    try:
                        efficiency_response = await get_machine_efficiency_at_ratio(template.id, ratio, db)
                        if efficiency_response and efficiency_response.get("effective_hashrate") and efficiency_response.get("power_consumption"):
                            valid_ratios.append(ratio)
                    except:
                        continue
                
                if valid_ratios:
                    available_ratios[template.model] = {
                        "min_ratio": min(valid_ratios),
                        "max_ratio": max(valid_ratios),
                        "valid_ratios": valid_ratios
                    }
                    
                    # Calculer l'intersection avec les ratios communs
                    if common_ratios is None:
                        common_ratios = set(valid_ratios)
                    else:
                        common_ratios = common_ratios.intersection(set(valid_ratios))
                        
            except Exception as e:
                print(f"Erreur pour machine {template.model}: {e}")
                continue
    
    if not available_ratios:
        raise HTTPException(status_code=500, detail="Impossible de récupérer les ratios disponibles")
    
    # Trier les ratios communs
    common_ratios_list = sorted(list(common_ratios)) if common_ratios else []
    
    # Récupérer le ratio courant du site
    current_ratio = 1.0  # Valeur par défaut
    current_ratio_type = 'nominal'
    
    if machines:
        # Prendre le ratio de la première machine qui a un ratio défini
        for machine in machines:
            if machine.optimal_ratio is not None:
                current_ratio = float(machine.optimal_ratio)
                current_ratio_type = machine.ratio_type or 'manual'
                break
    
    return {
        "site_id": site_id,
        "site_name": site.name,
        "machines": available_ratios,
        "common_ratios": common_ratios_list,
        "min_common_ratio": min(common_ratios_list) if common_ratios_list else None,
        "max_common_ratio": max(common_ratios_list) if common_ratios_list else None,
        "current_ratio": current_ratio,
        "current_ratio_type": current_ratio_type
    }


@router.get("/sites/{site_id}/machines/{instance_id}/available-ratios")
async def get_machine_available_ratios(site_id: int, instance_id: int, db: Session = Depends(get_db)):
    """Récupère les ratios disponibles pour une machine spécifique"""
    
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Vérifier que l'instance de machine existe
    machine_instance = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.id == instance_id,
        models.SiteMachineInstance.site_id == site_id
    ).first()
    
    if not machine_instance:
        raise HTTPException(status_code=404, detail="Machine non trouvée")
    
    # Récupérer le template de la machine
    template = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_instance.template_id,
        models.MachineTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template de machine non trouvé")
    
    # Tester différents ratios pour trouver les limites
    test_ratios = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5]
    valid_ratios = []
    
    try:
        from ..routes.efficiency import get_machine_efficiency_at_ratio
        
        for ratio in test_ratios:
            try:
                efficiency_response = await get_machine_efficiency_at_ratio(template.id, ratio, db)
                if efficiency_response and efficiency_response.get("effective_hashrate") and efficiency_response.get("power_consumption"):
                    valid_ratios.append(ratio)
            except:
                continue
        
        if not valid_ratios:
            raise HTTPException(status_code=500, detail="Impossible de récupérer les ratios disponibles")
        
        # Récupérer le ratio courant
        current_ratio = 1.0
        current_ratio_type = 'nominal'
        
        if machine_instance.optimal_ratio is not None:
            current_ratio = float(machine_instance.optimal_ratio)
            current_ratio_type = machine_instance.ratio_type or 'manual'
        
        return {
            "site_id": site_id,
            "instance_id": instance_id,
            "machine_model": template.model,
            "valid_ratios": valid_ratios,
            "min_ratio": min(valid_ratios),
            "max_ratio": max(valid_ratios),
            "current_ratio": current_ratio,
            "current_ratio_type": current_ratio_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des ratios: {str(e)}"
        )


@router.post("/sites/{site_id}/machines/{instance_id}/apply-ratio")
async def apply_ratio_to_machine(site_id: int, instance_id: int, ratio_data: dict, db: Session = Depends(get_db)):
    """Applique un ratio spécifique à une machine particulière"""
    
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Vérifier que l'instance de machine existe
    machine_instance = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.id == instance_id,
        models.SiteMachineInstance.site_id == site_id
    ).first()
    
    if not machine_instance:
        raise HTTPException(status_code=404, detail="Machine non trouvée")
    
    # Récupérer les données du ratio
    ratio = ratio_data.get("ratio")
    optimization_type = ratio_data.get("optimization_type", "economic")
    
    if ratio is None:
        raise HTTPException(status_code=400, detail="Ratio requis")
    
    # Validation basique
    if ratio < 0.5 or ratio > 1.5:
        raise HTTPException(status_code=400, detail="Ratio doit être entre 0.5 et 1.5")
    
    # Vérifier si le ratio est valide pour cette machine
    template = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_instance.template_id,
        models.MachineTemplate.is_active == True
    ).first()
    
    if template:
        try:
            from ..routes.efficiency import get_machine_efficiency_at_ratio
            efficiency_response = await get_machine_efficiency_at_ratio(template.id, ratio, db)
            
            if not efficiency_response or not efficiency_response.get("effective_hashrate") or not efficiency_response.get("power_consumption"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Ratio {ratio} non valide pour la machine {template.model}. "
                           f"Utilisez l'API /efficiency/machines/{template.id}/ratio-bounds pour voir les ratios disponibles."
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la validation du ratio {ratio}: {str(e)}"
            )
    
    # Appliquer le ratio à cette machine spécifique
    # Si le ratio est 1.0, c'est considéré comme nominal
    if ratio == 1.0:
        machine_instance.optimal_ratio = None
        machine_instance.ratio_type = 'nominal'
    else:
        machine_instance.optimal_ratio = ratio
        machine_instance.ratio_type = 'manual'
    
    db.commit()
    
    return {
        "message": f"Ratio {ratio} appliqué avec succès à la machine {template.model if template else 'Unknown'}",
        "instance_id": instance_id,
        "site_id": site_id,
        "ratio": ratio,
        "optimization_type": optimization_type
    }


@router.post("/sites/{site_id}/reset-to-nominal")
async def reset_to_nominal_ratio(site_id: int, db: Session = Depends(get_db)):
    """Réinitialiser toutes les machines d'un site au ratio nominal (1.0)"""
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Récupérer toutes les machines du site
    machines = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id
    ).all()
    
    instances_updated = 0
    total_machines = 0
    
    for machine in machines:
        # Réinitialiser au ratio nominal
        machine.optimal_ratio = None
        machine.ratio_type = 'nominal'
        instances_updated += 1
        total_machines += machine.quantity
    
    db.commit()
    
    return {
        "message": f"Ratio nominal (1.0) appliqué avec succès à {total_machines} machine(s) dans {instances_updated} instance(s)",
        "instances_updated": instances_updated,
        "total_machines": total_machines,
        "site_id": site_id
    } 