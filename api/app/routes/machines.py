from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from datetime import date

from ..database import get_db
from ..models import models
from ..models.schemas import MachineTemplate, MachineTemplateCreate, MachineTemplateUpdate

router = APIRouter()

@router.get("/machines", response_model=List[MachineTemplate])
async def get_machines(db: Session = Depends(get_db)):
    """Récupérer tous les templates de machines"""
    machines = db.query(models.MachineTemplate).filter(models.MachineTemplate.is_active == True).all()
    return machines

@router.get("/machines/{machine_id}", response_model=MachineTemplate)
async def get_machine(machine_id: int, db: Session = Depends(get_db)):
    """Récupérer un template de machine spécifique"""
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return machine

@router.post("/machines", response_model=MachineTemplate)
async def create_machine(machine: MachineTemplateCreate, db: Session = Depends(get_db)):
    """Créer un nouveau template de machine"""
    # Vérifier si le template existe déjà
    existing_machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.model == machine.model
    ).first()
    if existing_machine:
        raise HTTPException(status_code=400, detail="Un template avec ce modèle existe déjà")
    
    db_machine = models.MachineTemplate(**machine.dict())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

@router.put("/machines/{machine_id}", response_model=MachineTemplate)
async def update_machine(
    machine_id: int, 
    machine_update: MachineTemplateUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour un template de machine"""
    db_machine = db.query(models.MachineTemplate).filter(models.MachineTemplate.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Mettre à jour les champs fournis
    update_data = machine_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_machine, field, value)
    
    db.commit()
    db.refresh(db_machine)
    return db_machine

@router.delete("/machines/{machine_id}")
async def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    """Supprimer un template de machine (soft delete)"""
    db_machine = db.query(models.MachineTemplate).filter(models.MachineTemplate.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Soft delete - marquer comme inactif
    db_machine.is_active = False
    db.commit()
    return {"message": "Template supprimé avec succès"}

@router.get("/machines/{machine_id}/efficiency")
async def get_machine_efficiency(machine_id: int, db: Session = Depends(get_db)):
    """Récupérer les courbes d'efficacité d'un template de machine"""
    # Vérifier que le template existe
    machine = db.query(models.MachineTemplate).filter(
        models.MachineTemplate.id == machine_id,
        models.MachineTemplate.is_active == True
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    
    # Récupérer les courbes d'efficacité
    efficiency_curves = db.query(models.MachineEfficiencyCurve).filter(
        models.MachineEfficiencyCurve.machine_id == machine_id
    ).order_by(models.MachineEfficiencyCurve.power_consumption).all()
    
    return {
        "machine": machine,
        "efficiency_curves": efficiency_curves
    } 