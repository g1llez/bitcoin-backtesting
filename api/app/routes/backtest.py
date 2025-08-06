from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from datetime import date, timedelta
from decimal import Decimal
import statistics

from ..database import get_db
from ..models import models
from ..models.schemas import BacktestRequest, BacktestResponse, BacktestResult, DailySimulation

router = APIRouter()

@router.post("/backtest/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """Lancer un backtest pour une machine avec un ratio d'ajustement"""
    
    # Vérifier que la machine existe
    machine = db.query(models.MiningMachine).filter(models.MiningMachine.id == request.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine non trouvée")
    
    # Vérifier que les données nécessaires existent
    bitcoin_prices = db.query(models.BitcoinPrice).filter(
        models.BitcoinPrice.date >= request.start_date,
        models.BitcoinPrice.date <= request.end_date
    ).all()
    
    fpps_data = db.query(models.FppsData).filter(
        models.FppsData.date >= request.start_date,
        models.FppsData.date <= request.end_date
    ).all()
    
    if not bitcoin_prices:
        raise HTTPException(status_code=400, detail="Aucun prix Bitcoin trouvé pour cette période")
    
    if not fpps_data:
        raise HTTPException(status_code=400, detail="Aucune donnée FPPS trouvée pour cette période")
    
    # Créer le résultat de backtest
    backtest_result = models.BacktestResult(
        machine_id=request.machine_id,
        start_date=request.start_date,
        end_date=request.end_date,
        adjustment_ratio=request.adjustment_ratio,
        total_profit_usd=Decimal('0'),
        total_cost_usd=Decimal('0'),
        total_revenue_usd=Decimal('0'),
        roi_percentage=Decimal('0')
    )
    
    db.add(backtest_result)
    db.commit()
    db.refresh(backtest_result)
    
    # Calculer les résultats quotidiens
    daily_simulations = []
    total_profit = Decimal('0')
    total_cost = Decimal('0')
    total_revenue = Decimal('0')
    
    current_date = request.start_date
    while current_date <= request.end_date:
        # Trouver les données pour cette date
        bitcoin_price = next((p for p in bitcoin_prices if p.date == current_date), None)
        fpps_info = next((f for f in fpps_data if f.date == current_date), None)
        
        if bitcoin_price and fpps_info:
            # Récupérer l'efficacité de la machine pour ce ratio
            efficiency_result = db.execute(
                text("SELECT * FROM get_machine_efficiency_interpolated(:machine_id, :ratio)"),
                {"machine_id": request.machine_id, "ratio": request.adjustment_ratio}
            ).fetchone()
            
            if efficiency_result:
                effective_hashrate, power_consumption = efficiency_result
                
                # Calculer les revenus (en USD)
                daily_revenue_btc = (effective_hashrate * fpps_info.fpps_rate * 24) / fpps_info.network_difficulty
                daily_revenue_usd = daily_revenue_btc * bitcoin_price.price_usd
                
                # Calculer les coûts (en USD)
                daily_power_kwh = power_consumption * 24 / 1000  # kWh
                daily_cost_usd = daily_power_kwh * request.electricity_rate_cad * bitcoin_price.price_cad / bitcoin_price.price_usd
                
                # Calculer le profit
                daily_profit_usd = daily_revenue_usd - daily_cost_usd
                daily_roi = (daily_profit_usd / daily_cost_usd * 100) if daily_cost_usd > 0 else Decimal('0')
                
                # Créer l'enregistrement quotidien
                daily_sim = models.DailySimulation(
                    backtest_id=backtest_result.id,
                    date=current_date,
                    machine_id=request.machine_id,
                    adjustment_ratio=request.adjustment_ratio,
                    power_consumed_kwh=daily_power_kwh,
                    revenue_usd=daily_revenue_usd,
                    cost_usd=daily_cost_usd,
                    profit_usd=daily_profit_usd,
                    roi_daily=daily_roi
                )
                
                db.add(daily_sim)
                daily_simulations.append(daily_sim)
                
                # Accumuler les totaux
                total_revenue += daily_revenue_usd
                total_cost += daily_cost_usd
                total_profit += daily_profit_usd
        
        current_date += timedelta(days=1)
    
    # Mettre à jour le résultat de backtest
    backtest_result.total_revenue_usd = total_revenue
    backtest_result.total_cost_usd = total_cost
    backtest_result.total_profit_usd = total_profit
    backtest_result.roi_percentage = (total_profit / total_cost * 100) if total_cost > 0 else Decimal('0')
    
    db.commit()
    db.refresh(backtest_result)
    
    # Calculer les statistiques
    profits = [sim.profit_usd for sim in daily_simulations]
    summary = {
        "total_days": len(daily_simulations),
        "profitable_days": len([p for p in profits if p > 0]),
        "total_profit_usd": float(total_profit),
        "total_cost_usd": float(total_cost),
        "total_revenue_usd": float(total_revenue),
        "roi_percentage": float(backtest_result.roi_percentage),
        "avg_daily_profit": float(statistics.mean(profits)) if profits else 0,
        "max_daily_profit": float(max(profits)) if profits else 0,
        "min_daily_profit": float(min(profits)) if profits else 0,
        "profit_volatility": float(statistics.stdev(profits)) if len(profits) > 1 else 0
    }
    
    return BacktestResponse(
        backtest_result=backtest_result,
        daily_simulations=daily_simulations,
        summary=summary
    )

@router.get("/backtest/results", response_model=List[BacktestResult])
async def get_backtest_results(
    machine_id: int = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Récupérer les résultats de backtesting"""
    query = db.query(models.BacktestResult)
    
    if machine_id:
        query = query.filter(models.BacktestResult.machine_id == machine_id)
    
    results = query.order_by(models.BacktestResult.created_at.desc()).limit(limit).all()
    return results

@router.get("/backtest/results/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_result(backtest_id: int, db: Session = Depends(get_db)):
    """Récupérer un résultat de backtesting spécifique avec ses simulations quotidiennes"""
    backtest_result = db.query(models.BacktestResult).filter(
        models.BacktestResult.id == backtest_id
    ).first()
    
    if not backtest_result:
        raise HTTPException(status_code=404, detail="Résultat de backtest non trouvé")
    
    daily_simulations = db.query(models.DailySimulation).filter(
        models.DailySimulation.backtest_id == backtest_id
    ).order_by(models.DailySimulation.date).all()
    
    # Calculer les statistiques
    profits = [sim.profit_usd for sim in daily_simulations]
    summary = {
        "total_days": len(daily_simulations),
        "profitable_days": len([p for p in profits if p > 0]),
        "total_profit_usd": float(backtest_result.total_profit_usd),
        "total_cost_usd": float(backtest_result.total_cost_usd),
        "total_revenue_usd": float(backtest_result.total_revenue_usd),
        "roi_percentage": float(backtest_result.roi_percentage),
        "avg_daily_profit": float(statistics.mean(profits)) if profits else 0,
        "max_daily_profit": float(max(profits)) if profits else 0,
        "min_daily_profit": float(min(profits)) if profits else 0,
        "profit_volatility": float(statistics.stdev(profits)) if len(profits) > 1 else 0
    }
    
    return BacktestResponse(
        backtest_result=backtest_result,
        daily_simulations=daily_simulations,
        summary=summary
    ) 