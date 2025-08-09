import requests
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MarketCacheService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_cached_bitcoin_price(self) -> Optional[dict]:
        """Récupère le prix Bitcoin (CAD et USD) depuis le cache ou l'API"""
        try:
            # Essayer de récupérer depuis le cache
            result = self.db.execute(
                text("SELECT get_market_cache('bitcoin_price', 1)"),
            ).fetchone()
            
            if result and result[0]:
                cache_data = result[0]
                # Compat: ancien cache {price: cad}
                if cache_data.get('price') is not None:
                    return {"CAD": float(cache_data['price']), "USD": None}
                # Nouveau cache {CAD: x, USD: y}
                if cache_data.get('CAD') is not None or cache_data.get('USD') is not None:
                    return {"CAD": cache_data.get('CAD'), "USD": cache_data.get('USD')}
            
            # Si pas de cache valide, récupérer depuis l'API
            logger.info("Récupération du prix Bitcoin depuis l'API")
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=cad,usd",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                price_cad = data.get('bitcoin', {}).get('cad')
                price_usd = data.get('bitcoin', {}).get('usd')
                
                if price_cad or price_usd:
                    # Mettre en cache
                    cache_value = json.dumps({"CAD": price_cad, "USD": price_usd})
                    self.db.execute(
                        text("SELECT update_market_cache('bitcoin_price', :value)"),
                        {"value": cache_value}
                    )
                    self.db.commit()
                    return {"CAD": price_cad, "USD": price_usd}
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du prix Bitcoin: {e}")
            return None
    
    def get_cached_fpps_rate(self) -> Optional[float]:
        """Récupère le taux FPPS depuis le cache ou l'API"""
        try:
            # Essayer de récupérer depuis le cache
            result = self.db.execute(
                text("SELECT get_market_cache('fpps_rate', 1)"),
            ).fetchone()
            
            if result and result[0]:
                cache_data = result[0]
                if cache_data.get('rate') is not None:
                    logger.info("Taux FPPS récupéré depuis le cache")
                    return float(cache_data['rate'])
            
            # Si pas de cache valide, récupérer depuis l'API
            logger.info("Récupération du taux FPPS depuis l'API")
            
            # Récupérer le token depuis la configuration
            token_result = self.db.execute(
                text("SELECT value FROM app_config WHERE key = 'braiins_token'")
            ).fetchone()
            
            headers = {}
            if token_result and token_result[0]:
                headers["Pool-Auth-Token"] = token_result[0]
            
            response = requests.get(
                "https://pool.braiins.com/stats/json/btc",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                fpps_rate = data.get('btc', {}).get('fpps_rate')
                
                if fpps_rate:
                    # Mettre en cache
                    cache_value = json.dumps({"rate": fpps_rate, "unit": "BTC/day/TH/s"})
                    self.db.execute(
                        text("SELECT update_market_cache('fpps_rate', :value)"),
                        {"value": cache_value}
                    )
                    self.db.commit()
                    return float(fpps_rate)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du taux FPPS: {e}")
            return None
    
    def get_market_data(self) -> Dict[str, Any]:
        """Récupère toutes les données de marché (avec cache)"""
        bitcoin_prices = self.get_cached_bitcoin_price()
        fpps_rate = self.get_cached_fpps_rate()
        
        return {
            # Compat: bitcoin_price (CAD)
            "bitcoin_price": (bitcoin_prices.get("CAD") if bitcoin_prices else None),
            "bitcoin_price_cad": (bitcoin_prices.get("CAD") if bitcoin_prices else None),
            "bitcoin_price_usd": (bitcoin_prices.get("USD") if bitcoin_prices else None),
            "fpps_rate": fpps_rate,
            "fpps_sats_per_day": (fpps_rate * 100000000) if (fpps_rate is not None) else None,
            "fpps_sats": (int(round(fpps_rate * 100000000)) if (fpps_rate is not None) else None)
        }