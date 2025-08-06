from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..database import get_db
from ..models import models
from ..models.schemas import FppsData, FppsDataCreate, FppsDataUpdate

router = APIRouter()

@router.get("/fpps/data", response_model=List[FppsData])
async def get_fpps_data(
    start_date: date = None,
    end_date: date = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer les données FPPS historiques"""
    query = db.query(models.FppsData)
    
    if start_date:
        query = query.filter(models.FppsData.date >= start_date)
    if end_date:
        query = query.filter(models.FppsData.date <= end_date)
    
    data = query.order_by(models.FppsData.date.desc()).limit(limit).all()
    return data

@router.get("/fpps/data/{date}", response_model=FppsData)
async def get_fpps_data_by_date(date: date, db: Session = Depends(get_db)):
    """Récupérer les données FPPS pour une date spécifique"""
    data = db.query(models.FppsData).filter(models.FppsData.date == date).first()
    if not data:
        raise HTTPException(status_code=404, detail="Données FPPS non trouvées pour cette date")
    return data

@router.post("/fpps/data", response_model=FppsData)
async def create_fpps_data(data: FppsDataCreate, db: Session = Depends(get_db)):
    """Créer de nouvelles données FPPS"""
    # Vérifier si les données existent déjà pour cette date
    existing_data = db.query(models.FppsData).filter(
        models.FppsData.date == data.date
    ).first()
    
    if existing_data:
        raise HTTPException(status_code=400, detail="Des données FPPS existent déjà pour cette date")
    
    db_data = models.FppsData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

@router.put("/fpps/data/{date}", response_model=FppsData)
async def update_fpps_data(
    date: date, 
    data_update: FppsDataUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour les données FPPS pour une date"""
    db_data = db.query(models.FppsData).filter(models.FppsData.date == date).first()
    if not db_data:
        raise HTTPException(status_code=404, detail="Données FPPS non trouvées pour cette date")
    
    # Mettre à jour les champs fournis
    update_data = data_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_data, field, value)
    
    db.commit()
    db.refresh(db_data)
    return db_data

@router.delete("/fpps/data/{date}")
async def delete_fpps_data(date: date, db: Session = Depends(get_db)):
    """Supprimer les données FPPS pour une date"""
    db_data = db.query(models.FppsData).filter(models.FppsData.date == date).first()
    if not db_data:
        raise HTTPException(status_code=404, detail="Données FPPS non trouvées pour cette date")
    
    db.delete(db_data)
    db.commit()
    return {"message": "Données FPPS supprimées avec succès"}

@router.get("/fpps-data/count")
async def get_fpps_data_count(db: Session = Depends(get_db)):
    """Compter le nombre total de données FPPS"""
    count = db.query(models.FppsData).count()
    return count

@router.post("/fpps/data/bulk")
async def create_fpps_data_bulk(data_list: List[FppsDataCreate], db: Session = Depends(get_db)):
    """Créer plusieurs données FPPS en lot"""
    created_data = []
    errors = []
    
    for data in data_list:
        try:
            # Vérifier si les données existent déjà
            existing_data = db.query(models.FppsData).filter(
                models.FppsData.date == data.date
            ).first()
            
            if existing_data:
                errors.append(f"Données FPPS déjà existantes pour {data.date}")
                continue
            
            db_data = models.FppsData(**data.dict())
            db.add(db_data)
            created_data.append(db_data)
            
        except Exception as e:
            errors.append(f"Erreur pour {data.date}: {str(e)}")
    
    if created_data:
        db.commit()
        for data in created_data:
            db.refresh(data)
    
    return {
        "created": len(created_data),
        "errors": errors,
        "data": created_data
    } 