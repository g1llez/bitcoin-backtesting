from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configuration de la base de données (obligatoire, pas de valeur par défaut)
try:
    DATABASE_URL = os.environ["DATABASE_URL"]
except KeyError as exc:
    raise RuntimeError(
        "DATABASE_URL environment variable is required and must not use fallback values."
    ) from exc

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL)

# Création de la session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

def get_db():
    """Dependency pour obtenir la session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 