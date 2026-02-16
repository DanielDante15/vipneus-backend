# app/routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Dict
from datetime import datetime

from ..database import get_db
from ..models import Tire, Sale, Purchase, User
from ..auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna dados consolidados para o dashboard"""
    
    # Estatísticas gerais
    total_tires = db.query(Tire).filter(
        Tire.user_id == current_user.id,
        Tire.vendido == False
    ).count()
    
    total_sold = db.query(Sale).filter(
        Sale.user_id == current_user.id
    ).count()
    
    total_purchased = db.query(Purchase).filter(
        Purchase.user_id == current_user.id
    ).count()
    
    # Total entrada (compras)
    total_entrada = db.query(func.sum(Purchase.valor)).filter(
        Purchase.user_id == current_user.id
    ).scalar() or 0
    
    # Total saída (vendas)
    total_saida = db.query(func.sum(Sale.valor)).filter(
        Sale.user_id == current_user.id
    ).scalar() or 0
    
    # Calcular lucro real
    sales = db.query(Sale).filter(Sale.user_id == current_user.id).all()
    lucro = 0
    for sale in sales:
        tire = sale.tire
        if tire.purchase_id and tire.purchase:
            # Venda com custo: lucro = venda - custo
            lucro += sale.valor - tire.purchase.valor
        else:
            # Venda sem custo (pneu adicionado manualmente): lucro = valor total
            lucro += sale.valor
    
    # Pneus por condição
    condition_data = []
    conditions = db.query(
        Tire.condicao,
        func.count(Tire.id).label('count')
    ).filter(
        Tire.user_id == current_user.id,
        Tire.vendido == False
    ).group_by(Tire.condicao).all()
    
    condition_labels = {
        "novo": "Novo",
        "seminovo": "Seminovo",
        "recapado": "Recapado",
        "meia-vida": "Meia-vida"
    }
    
    for condition, count in conditions:
        condition_data.append({
            "name": condition_labels.get(condition, condition),
            "value": count
        })
    
    # Top 5 marcas mais vendidas
    top_brands = []
    brands = db.query(
        Tire.marca,
        func.count(Sale.id).label('count')
    ).join(Sale, Sale.tire_id == Tire.id).filter(
        Sale.user_id == current_user.id
    ).group_by(Tire.marca).order_by(func.count(Sale.id).desc()).limit(5).all()
    
    for marca, count in brands:
        top_brands.append({
            "name": marca,
            "value": count
        })
    
    # Dados mensais (vendas e compras)
    # Vendas por mês
    sales_monthly = {}
    sales_data = db.query(
        extract('year', Sale.data).label('year'),
        extract('month', Sale.data).label('month'),
        func.sum(Sale.valor).label('total')
    ).filter(
        Sale.user_id == current_user.id
    ).group_by('year', 'month').all()
    
    for year, month, total in sales_data:
        key = f"{int(year)}-{int(month):02d}"
        sales_monthly[key] = float(total or 0)
    
    # Compras por mês
    purchases_monthly = {}
    purchases_data = db.query(
        extract('year', Purchase.data).label('year'),
        extract('month', Purchase.data).label('month'),
        func.sum(Purchase.valor).label('total')
    ).filter(
        Purchase.user_id == current_user.id
    ).group_by('year', 'month').all()
    
    for year, month, total in purchases_data:
        key = f"{int(year)}-{int(month):02d}"
        purchases_monthly[key] = float(total or 0)
    
    # Combinar dados mensais
    all_months = set(sales_monthly.keys()) | set(purchases_monthly.keys())
    monthly_data = []
    for month in sorted(all_months):
        year, mon = month.split("-")
        monthly_data.append({
            "month": f"{mon}/{year}",
            "vendas": sales_monthly.get(month, 0),
            "compras": purchases_monthly.get(month, 0)
        })
    
    return {
        "stats": {
            "total_tires": total_tires,
            "total_sold": total_sold,
            "total_purchased": total_purchased,
            "total_entrada": float(total_entrada),
            "total_saida": float(total_saida),
            "lucro": float(lucro)
        },
        "condition_data": condition_data,
        "top_brands": top_brands,
        "monthly_data": monthly_data
    }