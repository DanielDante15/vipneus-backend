# app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import Sale, Purchase, Tire, User
from ..auth import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])

def get_month_format(db: Session):
    """Retorna a função SQL correta para formatar mês de acordo com o banco"""
    dialect = db.bind.dialect.name
    
    if dialect == "postgresql":
        # PostgreSQL usa to_char
        return func.to_char
    elif dialect == "sqlite":
        # SQLite usa strftime
        return func.strftime
    else:
        # Outros bancos (MySQL, etc)
        return func.date_format

@router.get("/months")
def get_available_months(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna lista de meses com vendas ou compras"""
    
    dialect = db.bind.dialect.name
    
    # Meses com vendas
    if dialect == "postgresql":
        sales_months = db.query(
            func.to_char(Sale.data, 'YYYY-MM').label('month')
        ).filter(
            Sale.user_id == current_user.id
        ).distinct().all()
        
        purchases_months = db.query(
            func.to_char(Purchase.data, 'YYYY-MM').label('month')
        ).filter(
            Purchase.user_id == current_user.id
        ).distinct().all()
    
    elif dialect == "sqlite":
        sales_months = db.query(
            func.strftime('%Y-%m', Sale.data).label('month')
        ).filter(
            Sale.user_id == current_user.id
        ).distinct().all()
        
        purchases_months = db.query(
            func.strftime('%Y-%m', Purchase.data).label('month')
        ).filter(
            Purchase.user_id == current_user.id
        ).distinct().all()
    
    else:
        # MySQL
        sales_months = db.query(
            func.date_format(Sale.data, '%Y-%m').label('month')
        ).filter(
            Sale.user_id == current_user.id
        ).distinct().all()
        
        purchases_months = db.query(
            func.date_format(Purchase.data, '%Y-%m').label('month')
        ).filter(
            Purchase.user_id == current_user.id
        ).distinct().all()
    
    # Combinar e ordenar
    all_months = set()
    for (month,) in sales_months:
        all_months.add(month)
    for (month,) in purchases_months:
        all_months.add(month)
    
    return {
        "months": sorted(list(all_months), reverse=True)
    }

@router.get("/monthly/{month}")
def get_monthly_report(
    month: str,  # Formato: YYYY-MM
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna relatório detalhado de um mês específico"""
    
    # Validar formato do mês
    try:
        year, mon = month.split("-")
        year = int(year)
        mon = int(mon)
        if mon < 1 or mon > 12:
            raise ValueError
    except:
        raise HTTPException(status_code=400, detail="Formato de mês inválido. Use YYYY-MM")
    
    dialect = db.bind.dialect.name
    
    # Buscar vendas do mês (usando funções específicas do banco)
    if dialect == "postgresql":
        # PostgreSQL: usar extract
        sales = db.query(Sale).filter(
            Sale.user_id == current_user.id,
            func.extract('year', Sale.data) == year,
            func.extract('month', Sale.data) == mon
        ).order_by(Sale.data.desc()).all()
        
        purchases = db.query(Purchase).filter(
            Purchase.user_id == current_user.id,
            func.extract('year', Purchase.data) == year,
            func.extract('month', Purchase.data) == mon
        ).order_by(Purchase.data.desc()).all()
    
    elif dialect == "sqlite":
        # SQLite: usar strftime
        sales = db.query(Sale).filter(
            Sale.user_id == current_user.id,
            func.strftime('%Y', Sale.data) == str(year),
            func.strftime('%m', Sale.data) == f"{mon:02d}"
        ).order_by(Sale.data.desc()).all()
        
        purchases = db.query(Purchase).filter(
            Purchase.user_id == current_user.id,
            func.strftime('%Y', Purchase.data) == str(year),
            func.strftime('%m', Purchase.data) == f"{mon:02d}"
        ).order_by(Purchase.data.desc()).all()
    
    else:
        # MySQL: usar YEAR() e MONTH()
        sales = db.query(Sale).filter(
            Sale.user_id == current_user.id,
            func.year(Sale.data) == year,
            func.month(Sale.data) == mon
        ).order_by(Sale.data.desc()).all()
        
        purchases = db.query(Purchase).filter(
            Purchase.user_id == current_user.id,
            func.year(Purchase.data) == year,
            func.month(Purchase.data) == mon
        ).order_by(Purchase.data.desc()).all()
    
    # Calcular totais
    total_vendas = sum(sale.valor for sale in sales)
    total_compras = sum(purchase.valor for purchase in purchases)
    
    # Calcular lucro real
    lucro = 0
    for sale in sales:
        tire = sale.tire
        if tire.purchase_id and tire.purchase:
            # Venda com custo
            lucro += sale.valor - tire.purchase.valor
        else:
            # Venda sem custo (pneu adicionado manualmente)
            lucro += sale.valor
    
    # Montar dados de vendas
    sales_data = []
    for sale in sales:
        tire = sale.tire
        custo = None
        lucro_individual = None
        
        if tire.purchase_id and tire.purchase:
            custo = tire.purchase.valor
            lucro_individual = sale.valor - custo
        else:
            lucro_individual = sale.valor
        
        sales_data.append({
            "id": sale.id,
            "data": sale.data.isoformat(),
            "marca": tire.marca,
            "medida": tire.medida,
            "aro": tire.aro,
            "valor": sale.valor,
            "custo": custo,
            "lucro": lucro_individual
        })
    
    # Montar dados de compras
    purchases_data = []
    for purchase in purchases:
        purchases_data.append({
            "id": purchase.id,
            "data": purchase.data.isoformat(),
            "marca": purchase.marca,
            "medida": purchase.medida,
            "aro": purchase.aro,
            "valor": purchase.valor
        })
    
    return {
        "month": month,
        "total_vendas": float(total_vendas),
        "total_compras": float(total_compras),
        "lucro": float(lucro),
        "sales_count": len(sales),
        "purchases_count": len(purchases),
        "sales": sales_data,
        "purchases": purchases_data
    }