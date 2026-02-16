# routes/purchases.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Purchase, Tire, User
from ..schemas import PurchaseCreate, PurchaseResponse
from ..auth import get_current_user

router = APIRouter(prefix="/purchases", tags=["purchases"])

@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase(
    purchase: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra uma compra E adiciona o pneu ao estoque"""
    
    # 1. Criar a compra
    new_purchase = Purchase(**purchase.dict(), user_id=current_user.id)
    db.add(new_purchase)
    db.flush()  # Gera o ID sem commitar
    
    # 2. Criar o pneu no estoque vinculado à compra
    new_tire = Tire(
        marca=purchase.marca,
        medida=purchase.medida,
        aro=purchase.aro,
        condicao=purchase.condicao,
        detalhes=purchase.detalhes,
        user_id=current_user.id,
        purchase_id=new_purchase.id  # Vincula à compra
    )
    db.add(new_tire)
    
    db.commit()
    db.refresh(new_purchase)
    return new_purchase

@router.get("/", response_model=List[PurchaseResponse])
def list_purchases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchases = db.query(Purchase).filter(
        Purchase.user_id == current_user.id
    ).order_by(Purchase.data.desc()).offset(skip).limit(limit).all()
    return purchases

@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchase = db.query(Purchase).filter(
        Purchase.id == purchase_id,
        Purchase.user_id == current_user.id
    ).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada")
    return purchase

@router.delete("/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase(
    purchase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deleta a compra E o pneu associado (se ainda não foi vendido)"""
    
    purchase = db.query(Purchase).filter(
        Purchase.id == purchase_id,
        Purchase.user_id == current_user.id
    ).first()
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra não encontrada")
    
    if purchase.tire and not purchase.tire.vendido:
        db.delete(purchase.tire)
    
    db.delete(purchase)
    db.commit()
    return None