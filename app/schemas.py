from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class TireCondition(str, Enum):
    novo = "novo"
    seminovo = "seminovo"
    recapado = "recapado"
    meia_vida = "meia-vida"

# ========== USER SCHEMAS ==========
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ========== TIRE SCHEMAS ==========
class TireBase(BaseModel):
    marca: str
    medida: str
    aro: str
    condicao: TireCondition
    detalhes: Optional[str] = None

class TireCreate(TireBase):
    pass

class TireUpdate(BaseModel):
    marca: Optional[str] = None
    medida: Optional[str] = None
    aro: Optional[str] = None
    condicao: Optional[TireCondition] = None
    detalhes: Optional[str] = None
    vendido: Optional[bool] = None
    data_saida: Optional[datetime] = None

class TireResponse(TireBase):
    id: str
    data_entrada: datetime
    data_saida: Optional[datetime] = None
    vendido: bool
    purchase_id: Optional[str] = None  # ← NOVO: Para rastrear se veio de uma compra
    
    class Config:
        from_attributes = True

# ========== PURCHASE SCHEMAS ==========
class PurchaseBase(BaseModel):
    valor: float = Field(gt=0, description="Valor deve ser maior que 0")
    marca: str
    medida: str
    aro: str
    condicao: TireCondition
    detalhes: Optional[str] = None

class PurchaseCreate(PurchaseBase):
    pass

# ← Resposta simplificada (sem o tire nested)
class PurchaseResponse(PurchaseBase):
    id: str
    data: datetime
    
    class Config:
        from_attributes = True

# ← OPCIONAL: Se quiser incluir dados do pneu criado
class PurchaseDetailResponse(PurchaseBase):
    id: str
    data: datetime
    tire: Optional[TireResponse] = None  # Pneu associado
    
    class Config:
        from_attributes = True

# ========== SALE SCHEMAS ==========
class SaleCreate(BaseModel):
    tire_id: str
    valor: float = Field(gt=0, description="Valor de venda deve ser maior que 0")

class SaleResponse(BaseModel):
    id: str
    tire_id: str
    valor: float
    data: datetime
    
    # ← NOVO: Dados do pneu vendido (para exibir)
    marca: str
    medida: str
    aro: str
    condicao: TireCondition
    
    # ← NOVO: Cálculo de lucro (se houver custo)
    custo: Optional[float] = None  # Custo da compra (se existir)
    lucro: Optional[float] = None 
    
    class Config:
        from_attributes = True

class SaleSimpleResponse(BaseModel):
    id: str
    tire_id: str
    valor: float
    data: datetime
    lucro: Optional[float] = None
    
    class Config:
        from_attributes = True