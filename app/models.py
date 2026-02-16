# models.py
from sqlalchemy import Boolean, Column, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from .database import Base

class TireConditionEnum(str, enum.Enum):
    novo = "novo"
    seminovo = "seminovo"
    recapado = "recapado"
    meia_vida = "meia-vida"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tires = relationship("Tire", back_populates="owner")
    sales = relationship("Sale", back_populates="owner")
    purchases = relationship("Purchase", back_populates="owner")

class Tire(Base):
    __tablename__ = "tires"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    marca = Column(String, nullable=False)
    medida = Column(String, nullable=False)
    aro = Column(String, nullable=False)
    condicao = Column(Enum(TireConditionEnum), nullable=False)
    data_entrada = Column(DateTime, default=datetime.utcnow)
    data_saida = Column(DateTime, nullable=True)
    detalhes = Column(String, nullable=True)
    vendido = Column(Boolean, default=False)
    
    # NOVA: FK opcional para compra (se veio de uma compra)
    purchase_id = Column(String, ForeignKey("purchases.id"), nullable=True)
    purchase = relationship("Purchase", back_populates="tire")
    
    user_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tires")

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tire_id = Column(String, ForeignKey("tires.id"), nullable=False)
    data = Column(DateTime, default=datetime.utcnow)
    valor = Column(Float, nullable=False)
    
    user_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="sales")
    tire = relationship("Tire", backref="sale")

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data = Column(DateTime, default=datetime.utcnow)
    valor = Column(Float, nullable=False)
    marca = Column(String, nullable=False)
    medida = Column(String, nullable=False)
    aro = Column(String, nullable=False)
    condicao = Column(Enum(TireConditionEnum), nullable=False)
    detalhes = Column(String, nullable=True)
    
    user_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="purchases")
    tire = relationship("Tire", back_populates="purchase", uselist=False)