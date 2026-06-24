from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import products, login, categories

# --- AGREGA ESTAS DOS LÍNEAS ---
from app.database import engine
from app import models
models.Base.metadata.create_all(bind=engine)
# -------------------------------

app = FastAPI(title="Catálogo API")

# ... resto de tu código CORS y rutas ....

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ¡AQUÍ ESTÁ LA MAGIA! Conectamos las rutas de products.py a nuestra app principal
app.include_router(products.router)
app.include_router(login.router)
app.include_router(categories.router)

@app.get("/")
def read_root():
    return {"mensaje": "¡El servidor FastAPI está funcionando correctamente!"}

# (Si tienes aquí el @app.get("/api/products") que hicimos para el buscador, déjalo tal cual)