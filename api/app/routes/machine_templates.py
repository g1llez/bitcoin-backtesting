from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import date

from ..database import get_db
from ..models import models
from ..models.schemas import MachineTemplate, MachineTemplateCreate, MachineTemplateUpdate
from ..models.schemas import SiteMachineInstance, SiteMachineInstanceCreate, SiteMachineInstanceUpdate

router = APIRouter()

# Routes pour les templates de machines
@router.get("/machine-templates", response_model=List[MachineTemplate])
async def get_machine_templates(db: Session = Depends(get_db)):
    """Récupérer tous les templates de machines"""
    templates = db.query(models.MachineTemplate).filter(models.MachineTemplate.is_active == True).all()
    return templates

@router.get("/machine-templates/{template_id}", response_model=MachineTemplate)
async def get_machine_template(template_id: int, db: Session = Depends(get_db)):
    """Récupérer un template spécifique"""
    template = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == template_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return template

@router.post("/machine-templates", response_model=MachineTemplate)
async def create_machine_template(template: MachineTemplateCreate, db: Session = Depends(get_db)):
    """Créer un nouveau template de machine"""
    # Vérifier si le template existe déjà
    existing_template = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.model == template.model
    ).first()
    if existing_template:
        raise HTTPException(status_code=400, detail="Un template avec ce modèle existe déjà")
    
    db_template = models.MachineTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.put("/machine-templates/{template_id}", response_model=MachineTemplate)
async def update_machine_template(
    template_id: int, 
    template_update: MachineTemplateUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour un template"""
    db_template = db.query(models.MachineTemplate).filter(models.MachineTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Mettre à jour les champs fournis
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/machine-templates/{template_id}")
async def delete_machine_template(template_id: int, db: Session = Depends(get_db)):
    """Supprimer un template (soft delete)"""
    db_template = db.query(models.MachineTemplate).filter(models.MachineTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Soft delete - marquer comme inactif
    db_template.is_active = False
    db.commit()
    return {"message": "Template supprimé avec succès"}

# Routes pour les instances de machines dans les sites
@router.get("/sites/{site_id}/machine-instances", response_model=List[SiteMachineInstance])
async def get_site_machine_instances(site_id: int, db: Session = Depends(get_db)):
    """Récupérer toutes les instances de machines d'un site"""
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    instances = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.site_id == site_id
    ).all()
    return instances

@router.post("/sites/{site_id}/machine-instances", response_model=SiteMachineInstance)
async def create_site_machine_instance(
    site_id: int, 
    instance: SiteMachineInstanceCreate, 
    db: Session = Depends(get_db)
):
    """Ajouter une instance de machine à un site"""
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Vérifier que le template existe
    template = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == instance.template_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Créer l'instance
    db_instance = models.SiteMachineInstance(
        site_id=site_id,
        **instance.dict()
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    return db_instance

@router.put("/sites/{site_id}/machine-instances/{instance_id}", response_model=SiteMachineInstance)
async def update_site_machine_instance(
    site_id: int,
    instance_id: int,
    instance_update: SiteMachineInstanceUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour une instance de machine"""
    db_instance = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.id == instance_id,
        models.SiteMachineInstance.site_id == site_id
    ).first()
    if not db_instance:
        raise HTTPException(status_code=404, detail="Instance non trouvée")
    
    # Mettre à jour les champs fournis
    update_data = instance_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_instance, field, value)
    
    db.commit()
    db.refresh(db_instance)
    return db_instance

@router.delete("/sites/{site_id}/machine-instances/{instance_id}")
async def delete_site_machine_instance(site_id: int, instance_id: int, db: Session = Depends(get_db)):
    """Supprimer une instance de machine d'un site"""
    db_instance = db.query(models.SiteMachineInstance).filter(
        models.SiteMachineInstance.id == instance_id,
        models.SiteMachineInstance.site_id == site_id
    ).first()
    if not db_instance:
        raise HTTPException(status_code=404, detail="Instance non trouvée")
    
    db.delete(db_instance)
    db.commit()
    return {"message": "Instance supprimée avec succès"}

# Route pour obtenir les statistiques d'un site
@router.get("/sites/{site_id}/statistics")
async def get_site_statistics(site_id: int, db: Session = Depends(get_db)):
    """Récupérer les statistiques d'un site (hashrate total, puissance, etc.)"""
    # Vérifier que le site existe
    site = db.query(models.MiningSite).filter(models.MiningSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Récupérer les instances avec leurs templates
    instances = db.query(models.SiteMachineInstance, models.MachineTemplate).join(
        models.MachineTemplate,
        models.SiteMachineInstance.template_id == models.MachineTemplate.id
    ).filter(
        models.SiteMachineInstance.site_id == site_id,
        models.MachineTemplate.is_active == True
    ).all()
    
    # Calculer les totaux
    total_hashrate = 0
    total_power = 0
    machines_count = 0
    
    for instance, template in instances:
        total_hashrate += template.hashrate_nominal * instance.quantity
        total_power += template.power_nominal * instance.quantity
        machines_count += instance.quantity
    
    return {
        "site_id": site_id,
        "site_name": site.name,
        "total_hashrate": float(total_hashrate),
        "total_power": total_power,
        "machines_count": machines_count,
        "instances": [
            {
                "id": instance.id,
                "template_id": template.id,
                "template_model": template.model,
                "quantity": instance.quantity,
                "custom_name": instance.custom_name,
                "hashrate": float(template.hashrate_nominal * instance.quantity),
                "power": template.power_nominal * instance.quantity
            }
            for instance, template in instances
        ]
    } 