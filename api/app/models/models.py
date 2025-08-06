from sqlalchemy import Column, Integer, String, Date, DECIMAL, TIMESTAMP, ForeignKey, BigInteger, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class BitcoinPrice(Base):
    """Modèle pour les prix historiques du Bitcoin"""
    __tablename__ = "bitcoin_prices"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    price_usd = Column(DECIMAL(15, 2), nullable=False)
    price_cad = Column(DECIMAL(15, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class FppsData(Base):
    """Modèle pour les données FPPS historiques"""
    __tablename__ = "fpps_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    fpps_rate = Column(DECIMAL(20, 8), nullable=False)  # Taux FPPS en BTC par TH/s
    network_difficulty = Column(BigInteger, nullable=False)
    network_hashrate = Column(DECIMAL(20, 2), nullable=False)  # TH/s
    block_reward = Column(DECIMAL(20, 8), nullable=False)  # BTC
    fees_total = Column(DECIMAL(20, 8), nullable=False)  # BTC
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class MachineTemplate(Base):
    """Modèle pour les templates de machines de mining Bitcoin"""
    __tablename__ = "machine_templates"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String(100), unique=True, nullable=False)
    manufacturer = Column(String(100), nullable=False)
    hashrate_nominal = Column(DECIMAL(15, 2), nullable=False)  # TH/s
    power_nominal = Column(Integer, nullable=False)  # Watts
    efficiency_base = Column(DECIMAL(10, 2), nullable=False)  # J/TH
    price_cad = Column(DECIMAL(10, 2))  # Prix en CAD
    release_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relations
    efficiency_curves = relationship("MachineEfficiencyCurve", back_populates="machine")
    backtest_results = relationship("BacktestResult", back_populates="machine")
    site_instances = relationship("SiteMachineInstance", back_populates="template")

class MachineEfficiencyCurve(Base):
    """Modèle pour les courbes d'efficacité des machines"""
    __tablename__ = "machine_efficiency_curves"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machine_templates.id"))
    effective_hashrate = Column(DECIMAL(15, 2), nullable=False)  # TH/s effectif (mesuré)
    power_consumption = Column(Integer, nullable=False)  # Watts consommés (mesurés)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relations
    machine = relationship("MachineTemplate", back_populates="efficiency_curves")

class BacktestResult(Base):
    """Modèle pour les résultats de backtesting"""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machine_templates.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    adjustment_ratio = Column(DECIMAL(5, 3), nullable=False)  # Ratio d'ajustement (0.5 à 1.0)
    total_profit_usd = Column(DECIMAL(15, 2), nullable=False)
    total_cost_usd = Column(DECIMAL(15, 2), nullable=False)
    total_revenue_usd = Column(DECIMAL(15, 2), nullable=False)
    roi_percentage = Column(DECIMAL(8, 4), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relations
    machine = relationship("MachineTemplate", back_populates="backtest_results")
    daily_simulations = relationship("DailySimulation", back_populates="backtest")

class DailySimulation(Base):
    """Modèle pour les résultats quotidiens détaillés"""
    __tablename__ = "daily_simulation"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtest_results.id"))
    date = Column(Date, nullable=False)
    machine_id = Column(Integer, ForeignKey("machine_templates.id"))
    adjustment_ratio = Column(DECIMAL(5, 3), nullable=False)
    power_consumed_kwh = Column(DECIMAL(10, 4), nullable=False)
    revenue_usd = Column(DECIMAL(15, 4), nullable=False)
    cost_usd = Column(DECIMAL(15, 4), nullable=False)
    profit_usd = Column(DECIMAL(15, 4), nullable=False)
    roi_daily = Column(DECIMAL(8, 4), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relations
    backtest = relationship("BacktestResult", back_populates="daily_simulations")

class AppConfig(Base):
    """Modèle pour la configuration de l'application"""
    __tablename__ = "app_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class MiningSite(Base):
    """Modèle pour les sites de minage"""
    __tablename__ = "mining_sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    electricity_tier1_rate = Column(DECIMAL(5, 4), default=0.0730)
    electricity_tier2_rate = Column(DECIMAL(5, 4), default=0.0890)
    electricity_tier1_limit = Column(Integer, default=40)
    braiins_token = Column(String(255))
    preferred_currency = Column(String(3), default="CAD")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    machine_instances = relationship("SiteMachineInstance", back_populates="site")

class SiteMachineInstance(Base):
    """Modèle pour les instances de machines dans les sites"""
    __tablename__ = "site_machine_instances"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("mining_sites.id", ondelete="CASCADE"))
    template_id = Column(Integer, ForeignKey("machine_templates.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=1)
    custom_name = Column(String(100))  # Nom personnalisé pour cette instance
    notes = Column(Text)  # Notes spécifiques à cette instance
    optimal_ratio = Column(DECIMAL(5, 3))  # Ratio d'ajustement optimal appliqué à cette instance
    ratio_type = Column(String(10), default='nominal')  # Type de ratio: manual, optimal, nominal
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    site = relationship("MiningSite", back_populates="machine_instances")
    template = relationship("MachineTemplate", back_populates="site_instances") 