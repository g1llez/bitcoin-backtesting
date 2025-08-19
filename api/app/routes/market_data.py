from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import subprocess
import json
import re
from typing import Dict, Any
from datetime import datetime
from ..database import get_db
from ..models import models
from ..services.market_cache import MarketCacheService
from sqlalchemy import text

router = APIRouter()

@router.get("/market/bitcoin-data")
async def get_bitcoin_market_data(db: Session = Depends(get_db)):
    """
    Récupère les données de marché Bitcoin (prix et FPPS)
    avec système de cache pour éviter les limites d'API
    """
    try:
        cache_service = MarketCacheService(db)
        market_data = cache_service.get_market_data()
        
        # Formater les données pour la compatibilité
        formatted_data = {
            "bitcoin_price_usd": market_data.get("bitcoin_price_usd"),
            "bitcoin_price_cad": market_data.get("bitcoin_price_cad"),
            "fpps_sats": market_data.get("fpps_sats"),
            "fpps_btc": market_data.get("fpps_rate"),
            "fpps_status": "real" if market_data.get("fpps_rate") else "cached_or_error"
        }
        
        return {
            "status": "success",
            "data": formatted_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données de marché: {str(e)}")



@router.get("/market/fpps")
async def get_fpps_data():
    """
    Récupère uniquement les données FPPS via le script check_braiins_fpps
    """
    try:
        # Récupérer le token depuis la configuration
        db = next(get_db())
        token_config = db.query(models.AppConfig).filter(models.AppConfig.key == "braiins_token").first()
        
        if not token_config or not token_config.value:
            # Retourner des données simulées si pas de token
            return {
                "fpps_sats": 48,
                "fpps_btc": 0.00000048,
                "status": "simulated_no_token",
                "timestamp": "2025-08-02T18:45:00Z"
            }
        
        # Appeler l'API Braiins directement
        import requests
        
        try:
            # Appeler l'API Braiins avec le token
            response = requests.get(
                "https://pool.braiins.com/stats/json/btc",
                headers={"Pool-Auth-Token": token_config.value},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                fpps_rate = data.get('btc', {}).get('fpps_rate')
                
                if fpps_rate:
                    # Convertir en sats (1 BTC = 100,000,000 sats)
                    fpps_sats = int(float(fpps_rate) * 100000000)
                    fpps_btc = fpps_sats / 100000000
                    
                    return {
                        "fpps_sats": fpps_sats,
                        "fpps_btc": fpps_btc,
                        "status": "real",
                        "timestamp": "2025-08-02T18:45:00Z"
                    }
                else:
                    raise Exception("FPPS non trouvé dans la réponse API")
            else:
                # En cas d'erreur HTTP, retourner des données simulées
                return {
                    "fpps_sats": 48,
                    "fpps_btc": 0.00000048,
                    "status": "simulated_error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "timestamp": "2025-08-02T18:45:00Z"
                }
                
        except requests.Timeout:
            return {
                "fpps_sats": 48,
                "fpps_btc": 0.00000048,
                "status": "simulated_timeout",
                "timestamp": "2025-08-02T18:45:00Z"
            }
        except Exception as e:
            return {
                "fpps_sats": 48,
                "fpps_btc": 0.00000048,
                "status": "simulated_error",
                "error": str(e),
                "timestamp": "2025-08-02T18:45:00Z"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données FPPS: {str(e)}")

@router.post("/market/cache/clear")
async def clear_market_cache(db: Session = Depends(get_db)):
    """
    Vide le cache des données de marché pour forcer un refresh
    """
    try:
        # Supprimer toutes les entrées du cache
        db.execute(text("DELETE FROM market_cache"))
        db.commit()
        
        return {
            "status": "success",
            "message": "Cache des données de marché vidé avec succès",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du vidage du cache: {str(e)}")

@router.get("/market/cache/status")
async def get_cache_status(db: Session = Depends(get_db)):
    """
    Récupère le statut du cache des données de marché
    """
    try:
        # Récupérer les informations du cache
        cache_info = db.execute(text("""
            SELECT 
                cache_key,
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - updated_at))/60 as age_minutes
            FROM market_cache
            ORDER BY cache_key
        """)).fetchall()
        
        return {
            "status": "success",
            "cache_info": [
                {
                    "key": row[0],
                    "updated_at": row[1].isoformat() if row[1] else None,
                    "age_minutes": round(row[2], 2) if row[2] else None
                }
                for row in cache_info
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du statut du cache: {str(e)}") 