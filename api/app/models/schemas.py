from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal

# Schémas pour MachineTemplate
class MachineTemplateBase(BaseModel):
    model: str = Field(..., max_length=100)
    manufacturer: str = Field(..., max_length=100)
    hashrate_nominal: Decimal = Field(..., ge=0)
    power_nominal: int = Field(..., gt=0)
    efficiency_base: Decimal = Field(..., ge=0)
    price_cad: Optional[Decimal] = Field(None, ge=0)  # Prix en CAD
    release_date: Optional[date] = None
    is_active: bool = True

class MachineTemplateCreate(MachineTemplateBase):
    pass

class MachineTemplateUpdate(BaseModel):
    manufacturer: Optional[str] = Field(None, max_length=100)
    hashrate_nominal: Optional[Decimal] = Field(None, ge=0)
    power_nominal: Optional[int] = Field(None, gt=0)
    efficiency_base: Optional[Decimal] = Field(None, ge=0)
    price_cad: Optional[Decimal] = Field(None, ge=0)  # Prix en CAD
    release_date: Optional[date] = None
    is_active: Optional[bool] = None

class MachineTemplate(MachineTemplateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schémas pour MachineEfficiencyCurve
class MachineEfficiencyCurveBase(BaseModel):
    machine_id: int
    effective_hashrate: Decimal = Field(..., ge=0)  # TH/s effectif (mesuré)
    power_consumption: int = Field(..., gt=0)  # Watts consommés (mesurés)

class MachineEfficiencyCurveCreate(MachineEfficiencyCurveBase):
    pass

class MachineEfficiencyCurveUpdate(BaseModel):
    effective_hashrate: Optional[Decimal] = Field(None, ge=0)
    power_consumption: Optional[int] = Field(None, gt=0)

class MachineEfficiencyCurve(MachineEfficiencyCurveBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schémas pour BitcoinPrice
class BitcoinPriceBase(BaseModel):
    date: date
    price_usd: Decimal = Field(..., ge=0)
    price_cad: Decimal = Field(..., ge=0)

class BitcoinPriceCreate(BitcoinPriceBase):
    pass

class BitcoinPriceUpdate(BaseModel):
    price_usd: Optional[Decimal] = Field(None, ge=0)
    price_cad: Optional[Decimal] = Field(None, ge=0)

class BitcoinPrice(BitcoinPriceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schémas pour FppsData
class FppsDataBase(BaseModel):
    date: date
    fpps_rate: Decimal = Field(..., ge=0)
    network_difficulty: int = Field(..., gt=0)
    network_hashrate: Decimal = Field(..., ge=0)
    block_reward: Decimal = Field(..., ge=0)
    fees_total: Decimal = Field(..., ge=0)

class FppsDataCreate(FppsDataBase):
    pass

class FppsDataUpdate(BaseModel):
    fpps_rate: Optional[Decimal] = Field(None, ge=0)
    network_difficulty: Optional[int] = Field(None, gt=0)
    network_hashrate: Optional[Decimal] = Field(None, ge=0)
    block_reward: Optional[Decimal] = Field(None, ge=0)
    fees_total: Optional[Decimal] = Field(None, ge=0)

class FppsData(FppsDataBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schémas pour BacktestResult
class BacktestResultBase(BaseModel):
    machine_id: int
    start_date: date
    end_date: date
    adjustment_ratio: Decimal = Field(..., ge=0.5, le=1.0)
    total_profit_usd: Decimal = Field(..., ge=0)
    total_cost_usd: Decimal = Field(..., ge=0)
    total_revenue_usd: Decimal = Field(..., ge=0)
    roi_percentage: Decimal = Field(..., ge=0)

class BacktestResultCreate(BacktestResultBase):
    pass

class BacktestResult(BacktestResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schémas pour DailySimulation
class DailySimulationBase(BaseModel):
    backtest_id: int
    date: date
    machine_id: int
    adjustment_ratio: Decimal = Field(..., ge=0.5, le=1.0)
    power_consumed_kwh: Decimal = Field(..., ge=0)
    revenue_usd: Decimal = Field(..., ge=0)
    cost_usd: Decimal = Field(..., ge=0)
    profit_usd: Decimal = Field(..., ge=0)
    roi_daily: Decimal = Field(..., ge=0)

class DailySimulationCreate(DailySimulationBase):
    pass

class DailySimulation(DailySimulationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Schémas pour les requêtes de backtesting
class BacktestRequest(BaseModel):
    machine_id: int
    start_date: date
    end_date: date
    adjustment_ratio: Decimal = Field(..., ge=0.5, le=1.0)
    electricity_rate_cad: Decimal = Field(..., ge=0)  # $/kWh

class BacktestResponse(BaseModel):
    backtest_result: BacktestResult
    daily_simulations: List[DailySimulation]
    summary: dict

# Schémas pour les statistiques
class BacktestSummary(BaseModel):
    total_days: int
    profitable_days: int
    total_profit_usd: Decimal
    total_cost_usd: Decimal
    total_revenue_usd: Decimal
    roi_percentage: Decimal
    avg_daily_profit: Decimal
    max_daily_profit: Decimal
    min_daily_profit: Decimal
    profit_volatility: Decimal

# Configuration
class AppConfigBase(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None

class AppConfigCreate(AppConfigBase):
    pass

class AppConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None

class AppConfig(AppConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Sites de minage
class MiningSiteBase(BaseModel):
    name: str
    address: Optional[str] = None
    electricity_tier1_rate: Optional[Decimal] = Field(None, ge=0)
    electricity_tier2_rate: Optional[Decimal] = Field(None, ge=0)
    electricity_tier1_limit: int = Field(..., gt=0)
    braiins_token: Optional[str] = None
    preferred_currency: str = "CAD"

class MiningSiteCreate(MiningSiteBase):
    pass

class MiningSiteUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    electricity_tier1_rate: Optional[Decimal] = Field(None, ge=0)
    electricity_tier2_rate: Optional[Decimal] = Field(None, ge=0)
    electricity_tier1_limit: Optional[int] = Field(None, gt=0)
    braiins_token: Optional[str] = None
    preferred_currency: Optional[str] = None

class MiningSite(MiningSiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Liaison sites-machines
class SiteMachineInstanceBase(BaseModel):
    template_id: int
    quantity: int = Field(..., gt=0)
    custom_name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class SiteMachineInstanceCreate(SiteMachineInstanceBase):
    pass

class SiteMachineInstanceUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    custom_name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class SiteMachineInstance(SiteMachineInstanceBase):
    id: int
    site_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 