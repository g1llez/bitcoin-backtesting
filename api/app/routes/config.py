from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from decimal import Decimal
import subprocess
import re

from ..database import get_db
from ..models import models
from ..models.schemas import AppConfig, AppConfigCreate, AppConfigUpdate

router = APIRouter()

@router.get("/config", response_model=List[AppConfig])
async def get_all_config(db: Session = Depends(get_db)):
    """Récupérer toute la configuration"""
    configs = db.query(models.AppConfig).all()
    return configs

@router.get("/config/{key}", response_model=AppConfig)
async def get_config(key: str, db: Session = Depends(get_db)):
    """Récupérer une configuration spécifique"""
    config = db.query(models.AppConfig).filter(models.AppConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config

@router.post("/config", response_model=AppConfig)
async def create_config(config: AppConfigCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle configuration"""
    # Vérifier si la clé existe déjà
    existing = db.query(models.AppConfig).filter(models.AppConfig.key == config.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Cette clé de configuration existe déjà")
    
    db_config = models.AppConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.put("/config/{key}", response_model=AppConfig)
async def update_config(key: str, config_update: AppConfigUpdate, db: Session = Depends(get_db)):
    """Mettre à jour une configuration"""
    db_config = db.query(models.AppConfig).filter(models.AppConfig.key == key).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

@router.delete("/config/{key}")
async def delete_config(key: str, db: Session = Depends(get_db)):
    """Supprimer une configuration"""
    db_config = db.query(models.AppConfig).filter(models.AppConfig.key == key).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    
    db.delete(db_config)
    db.commit()
    return {"message": "Configuration supprimée avec succès"}

# Route pour récupérer la configuration complète de l'application
@router.get("/config/app/settings")
async def get_app_settings(db: Session = Depends(get_db)):
    """Récupérer tous les paramètres de l'application"""
    configs = db.query(models.AppConfig).all()
    
    settings = {}
    for config in configs:
        settings[config.key] = config.value
    
    return {
        "settings": settings,
        "defaults": {
            "theme": "dark",
            "braiins_token": "",
            "preferred_currency": "CAD"
        }
    }

# Route pour mettre à jour plusieurs configurations à la fois
@router.post("/config/app/settings")
async def update_app_settings(settings: Dict[str, Any], db: Session = Depends(get_db)):
    """Mettre à jour plusieurs paramètres de l'application"""
    updated_configs = []
    
    for key, value in settings.items():
        # Vérifier si la configuration existe
        db_config = db.query(models.AppConfig).filter(models.AppConfig.key == key).first()
        
        if db_config:
            # Mettre à jour
            db_config.value = str(value)
            updated_configs.append(key)
        else:
            # Créer nouvelle configuration
            new_config = models.AppConfig(key=key, value=str(value))
            db.add(new_config)
            updated_configs.append(key)
    
    db.commit()
    
    return {
        "message": f"{len(updated_configs)} configurations mises à jour",
        "updated_keys": updated_configs
    }

# Route pour tester la connexion Braiins
@router.post("/config/test-braiins")
async def test_braiins_connection(token: str, db: Session = Depends(get_db)):
    """Tester la connexion à l'API Braiins Pool directement"""
    try:
        import requests
        
        # Appeler l'API Braiins avec le token
        response = requests.get(
            "https://pool.braiins.com/stats/json/btc",
            headers={"Pool-Auth-Token": token},
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                fpps_rate = data.get('btc', {}).get('fpps_rate')
                
                if fpps_rate:
                    # Convertir en sats (1 BTC = 100,000,000 sats)
                    fpps_sats = int(float(fpps_rate) * 100000000)
                    return {
                        "success": True,
                        "message": f"Connexion réussie - FPPS actuel: {fpps_sats} sats",
                        "fpps_sats": fpps_sats,
                        "fpps_btc": fpps_sats / 100000000
                    }
                else:
                    return {
                        "success": True,
                        "message": "Connexion réussie mais FPPS non trouvé dans la réponse",
                        "details": data
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": "Erreur lors du parsing de la réponse JSON",
                    "details": f"Erreur: {str(e)}, Réponse: {response.text[:200]}"
                }
        else:
            # Analyser l'erreur HTTP
            if response.status_code == 401:
                return {
                    "success": False,
                    "message": "Token invalide ou erreur d'authentification",
                    "details": response.text
                }
            else:
                return {
                    "success": False,
                    "message": f"Erreur HTTP {response.status_code} lors de la connexion à l'API Braiins",
                    "details": response.text
                }
                
    except requests.Timeout:
        return {
            "success": False,
            "message": "Timeout lors de la connexion à l'API Braiins"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors du test: {str(e)}"
        } 