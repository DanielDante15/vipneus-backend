from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Tire, User
from ..schemas import TireCreate, TireUpdate, TireResponse, TireCondition
from ..auth import get_current_user

router = APIRouter(prefix="/tires", tags=["tires"])

@router.post("/", response_model=TireResponse, status_code=status.HTTP_201_CREATED)
def create_tire(
    tire: TireCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_tire = Tire(**tire.dict(), user_id=current_user.id)
    db.add(new_tire)
    db.commit()
    db.refresh(new_tire)
    return new_tire

@router.get("/available", response_model=List[TireResponse])  # ← MOVER ANTES DO /{tire_id}
def list_available_tires(
    marca: Optional[str] = Query(None, description="Filtrar por marca"),
    medida: Optional[str] = Query(None, description="Filtrar por medida"),
    condicao: Optional[TireCondition] = Query(None, description="Filtrar por condição"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar apenas pneus disponíveis (não vendidos) com filtros"""
    
    query = db.query(Tire).filter(
        Tire.user_id == current_user.id,
        Tire.vendido == False  # Apenas não vendidos
    )
    
    # Aplicar filtros
    if marca and marca.lower() != "todas":
        query = query.filter(Tire.marca.ilike(f"%{marca}%"))
    
    if medida and medida.lower() != "todas":
        query = query.filter(Tire.medida == medida)
    
    if condicao and str(condicao).lower() != "todas":
        query = query.filter(Tire.condicao == condicao)
    
    tires = query.offset(skip).limit(limit).all()
    return tires

@router.get("/", response_model=List[TireResponse])
def list_tires(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tires = db.query(Tire).filter(Tire.user_id == current_user.id).offset(skip).limit(limit).all()
    return tires

@router.get("/{tire_id}", response_model=TireResponse)
def get_tire(
    tire_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tire = db.query(Tire).filter(Tire.id == tire_id, Tire.user_id == current_user.id).first()
    if not tire:
        raise HTTPException(status_code=404, detail="Pneu não encontrado")
    return tire

@router.put("/{tire_id}", response_model=TireResponse)
def update_tire(
    tire_id: str,
    tire_update: TireUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tire = db.query(Tire).filter(Tire.id == tire_id, Tire.user_id == current_user.id).first()
    if not tire:
        raise HTTPException(status_code=404, detail="Pneu não encontrado")
    
    for key, value in tire_update.dict(exclude_unset=True).items():
        setattr(tire, key, value)
    
    db.commit()
    db.refresh(tire)
    return tire

@router.delete("/{tire_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tire(
    tire_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tire = db.query(Tire).filter(Tire.id == tire_id, Tire.user_id == current_user.id).first()
    if not tire:
        raise HTTPException(status_code=404, detail="Pneu não encontrado")
    
    db.delete(tire)
    db.commit()
    return None