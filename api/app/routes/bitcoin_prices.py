from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from ..database import get_db
from ..models import models
from ..models.schemas import BitcoinPrice, BitcoinPriceCreate, BitcoinPriceUpdate

router = APIRouter()

@router.get("/bitcoin/prices", response_model=List[BitcoinPrice])
async def get_bitcoin_prices(
    start_date: date = None,
    end_date: date = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer les prix historiques du Bitcoin"""
    query = db.query(models.BitcoinPrice)
    
    if start_date:
        query = query.filter(models.BitcoinPrice.date >= start_date)
    if end_date:
        query = query.filter(models.BitcoinPrice.date <= end_date)
    
    prices = query.order_by(models.BitcoinPrice.date.desc()).limit(limit).all()
    return prices

@router.get("/bitcoin/prices/{date}", response_model=BitcoinPrice)
async def get_bitcoin_price(date: date, db: Session = Depends(get_db)):
    """Récupérer le prix du Bitcoin pour une date spécifique"""
    price = db.query(models.BitcoinPrice).filter(models.BitcoinPrice.date == date).first()
    if not price:
        raise HTTPException(status_code=404, detail="Prix non trouvé pour cette date")
    return price

@router.post("/bitcoin/prices", response_model=BitcoinPrice)
async def create_bitcoin_price(price: BitcoinPriceCreate, db: Session = Depends(get_db)):
    """Créer un nouveau prix Bitcoin"""
    # Vérifier si le prix existe déjà pour cette date
    existing_price = db.query(models.BitcoinPrice).filter(
        models.BitcoinPrice.date == price.date
    ).first()
    
    if existing_price:
        raise HTTPException(status_code=400, detail="Un prix existe déjà pour cette date")
    
    db_price = models.BitcoinPrice(**price.dict())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price

@router.put("/bitcoin/prices/{date}", response_model=BitcoinPrice)
async def update_bitcoin_price(
    date: date, 
    price_update: BitcoinPriceUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour le prix Bitcoin pour une date"""
    db_price = db.query(models.BitcoinPrice).filter(models.BitcoinPrice.date == date).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Prix non trouvé pour cette date")
    
    # Mettre à jour les champs fournis
    update_data = price_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_price, field, value)
    
    db.commit()
    db.refresh(db_price)
    return db_price

@router.delete("/bitcoin/prices/{date}")
async def delete_bitcoin_price(date: date, db: Session = Depends(get_db)):
    """Supprimer le prix Bitcoin pour une date"""
    db_price = db.query(models.BitcoinPrice).filter(models.BitcoinPrice.date == date).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Prix non trouvé pour cette date")
    
    db.delete(db_price)
    db.commit()
    return {"message": "Prix supprimé avec succès"}

@router.get("/bitcoin-prices/count")
async def get_bitcoin_prices_count(db: Session = Depends(get_db)):
    """Compter le nombre total de prix Bitcoin"""
    count = db.query(models.BitcoinPrice).count()
    return count

@router.post("/bitcoin/prices/bulk")
async def create_bitcoin_prices_bulk(prices: List[BitcoinPriceCreate], db: Session = Depends(get_db)):
    """Créer plusieurs prix Bitcoin en lot"""
    created_prices = []
    errors = []
    
    for price in prices:
        try:
            # Vérifier si le prix existe déjà
            existing_price = db.query(models.BitcoinPrice).filter(
                models.BitcoinPrice.date == price.date
            ).first()
            
            if existing_price:
                errors.append(f"Prix déjà existant pour {price.date}")
                continue
            
            db_price = models.BitcoinPrice(**price.dict())
            db.add(db_price)
            created_prices.append(db_price)
            
        except Exception as e:
            errors.append(f"Erreur pour {price.date}: {str(e)}")
    
    if created_prices:
        db.commit()
        for price in created_prices:
            db.refresh(price)
    
    return {
        "created": len(created_prices),
        "errors": errors,
        "prices": created_prices
    } 