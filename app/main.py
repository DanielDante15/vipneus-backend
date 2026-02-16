from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, tires, sales, purchases, dashboard,reports

# Cria as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Gestão de Pneus",
    description="API REST para gerenciamento de pneus, vendas e compras",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(auth.router)
app.include_router(tires.router)
app.include_router(sales.router)
app.include_router(purchases.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.get("/")
def read_root():
    return {
        "message": "API Gestão de Pneus",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}