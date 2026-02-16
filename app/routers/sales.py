# app/routers/sales.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import Sale, Tire, User
from ..schemas import SaleCreate, SaleResponse
from ..auth import get_current_user

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra uma venda e marca o pneu como vendido"""
    
    tire = db.query(Tire).filter(
        Tire.id == sale.tire_id,
        Tire.user_id == current_user.id
    ).first()
    
    if not tire:
        raise HTTPException(status_code=404, detail="Pneu não encontrado")
    
    if tire.vendido:
        raise HTTPException(status_code=400, detail="Pneu já foi vendido")
    
    new_sale = Sale(
        tire_id=sale.tire_id,
        valor=sale.valor,
        user_id=current_user.id
    )
    
    tire.vendido = True
    tire.data_saida = datetime.utcnow()
    
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    
    custo = None
    lucro = None
    if tire.purchase_id and tire.purchase:
        custo = tire.purchase.valor
        lucro = sale.valor - custo
    
    return {
        "id": new_sale.id,
        "tire_id": new_sale.tire_id,
        "valor": new_sale.valor,
        "data": new_sale.data,
        "marca": tire.marca,
        "medida": tire.medida,
        "aro": tire.aro,
        "condicao": tire.condicao,
        "custo": custo,
        "lucro": lucro
    }

@router.get("/", response_model=List[SaleResponse])
def list_sales(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sales = db.query(Sale).filter(
        Sale.user_id == current_user.id
    ).order_by(Sale.data.desc()).offset(skip).limit(limit).all()
    
    result = []
    for sale in sales:
        tire = sale.tire
        
        custo = None
        lucro = None
        if tire.purchase_id and tire.purchase:
            custo = tire.purchase.valor
            lucro = sale.valor - custo
        
        result.append({
            "id": sale.id,
            "tire_id": sale.tire_id,
            "valor": sale.valor,
            "data": sale.data,
            "marca": tire.marca,
            "medida": tire.medida,
            "aro": tire.aro,
            "condicao": tire.condicao,
            "custo": custo,
            "lucro": lucro
        })
    
    return result

@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.user_id == current_user.id
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    tire = sale.tire
    
    custo = None
    lucro = None
    if tire.purchase_id and tire.purchase:
        custo = tire.purchase.valor
        lucro = sale.valor - custo
    
    return {
        "id": sale.id,
        "tire_id": sale.tire_id,
        "valor": sale.valor,
        "data": sale.data,
        "marca": tire.marca,
        "medida": tire.medida,
        "aro": tire.aro,
        "condicao": tire.condicao,
        "custo": custo,
        "lucro": lucro
    }