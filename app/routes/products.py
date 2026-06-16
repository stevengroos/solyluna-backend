import httpx

# --- OPCIÓN NUCLEAR V2 (Para httpx / Supabase) ---
# Interceptamos el cliente HTTP que usa Supabase por debajo y le apagamos el SSL
_original_client_init = httpx.Client.__init__
def _patched_client_init(self, *args, **kwargs):
    kwargs['verify'] = False # ¡Apagamos la seguridad localmente!
    _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_client_init

_original_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init
# -------------------------------------------------
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Product
from supabase import create_client, Client
from app.auth import get_current_admin
import time

router = APIRouter()

# Reemplaza esto con tus credenciales reales de Supabase
SUPABASE_URL = "https://fpjuanavqjfpcmjmapjp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwanVhbmF2cWpmcGNtam1hcGpwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTQ4NTU3OSwiZXhwIjoyMDk3MDYxNTc5fQ.BUoe9eEVV6LD0wbKOfxk_o7_m66b3W64BMaqWNS0KfA"

# Inicializamos el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.post("/api/products")
async def create_product(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(...),
    category_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    admin_user: str = Depends(get_current_admin)
):
    try:
        file_bytes = await image.read()
        
        # 1. Limpiamos el nombre (quitamos espacios) y le ponemos un número único
        safe_filename = image.filename.replace(" ", "_")
        file_name = f"prod_{int(time.time())}_{safe_filename}" 
        
        # 2. Subimos a Supabase permitiendo sobreescritura (upsert) por si acaso
        supabase.storage.from_("productos-imagenes").upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": image.content_type, "upsert": "true"}
        )
        
        # 3. Obtener la URL pública
        public_url = supabase.storage.from_("productos-imagenes").get_public_url(file_name)
        
        # 4. Guardar en Postgres
        new_product = Product(
            title=title,
            description=description,
            price=price,
            stock=stock,
            image_url=public_url,
            category_id=category_id
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        return new_product

    except Exception as e:
        # ESTO ES VITAL: Imprimirá el error real en tu terminal negra
        print(f"\n❌ ERROR EXACTO DE SUPABASE: {str(e)}\n") 
        raise HTTPException(status_code=500, detail=f"Error al subir: {str(e)}")
    
@router.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    # Buscamos absolutamente todos los productos guardados en la tabla de Postgres
    products = db.query(Product).all()
    return products


class StockUpdate(BaseModel):
    stock: int

@router.put("/api/products/{product_id}/stock")
def update_stock(
    product_id: int, 
    stock_data: StockUpdate, 
    db: Session = Depends(get_db),
    admin_user: str = Depends(get_current_admin) # Exige el Token del admin
):
    producto = db.query(Product).filter(Product.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    producto.stock = stock_data.stock
    db.commit()
    return {"message": "Stock actualizado", "nuevo_stock": producto.stock}


class CategoryUpdate(BaseModel):
    category_id: Optional[int] = None

@router.put("/api/products/{product_id}/category")
def update_product_category(
    product_id: int, 
    category_data: CategoryUpdate, 
    db: Session = Depends(get_db),
    admin_user: str = Depends(get_current_admin)
):
    producto = db.query(Product).filter(Product.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    producto.category_id = category_data.category_id
    db.commit()
    return {"message": "Categoría actualizada con éxito"}

@router.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    producto = db.query(Product).filter(Product.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/api/products/{product_id}")
async def edit_product(
    product_id: int,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None), # <-- Es opcional
    db: Session = Depends(get_db),
    admin_user: str = Depends(get_current_admin)
):
    try:
        producto = db.query(Product).filter(Product.id == product_id).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Actualizamos los datos de texto
        producto.title = title
        producto.description = description
        producto.price = price
        producto.category_id = category_id

        # Si el usuario subió una imagen nueva, la procesamos
        if image and image.filename:
            file_bytes = await image.read()
            safe_filename = image.filename.replace(" ", "_")
            file_name = f"prod_{int(time.time())}_{safe_filename}" 
            
            supabase.storage.from_("productos-imagenes").upload(
                path=file_name,
                file=file_bytes,
                file_options={"content-type": image.content_type, "upsert": "true"}
            )
            public_url = supabase.storage.from_("productos-imagenes").get_public_url(file_name)
            producto.image_url = public_url # Reemplazamos la URL vieja por la nueva

        db.commit()
        db.refresh(producto)
        return producto

    except Exception as e:
        print(f"\n❌ ERROR DE EDICIÓN: {str(e)}\n") 
        raise HTTPException(status_code=500, detail=f"Error al editar: {str(e)}")