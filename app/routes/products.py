import httpx
import time
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Product, ProductVariant
from supabase import create_client, Client
from app.auth import get_current_admin

# --- PARCHE DE SEGURIDAD PARA SUPABASE LOCAL ---
_original_client_init = httpx.Client.__init__
def _patched_client_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_client_init

_original_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _original_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init
# -------------------------------------------------

router = APIRouter()

SUPABASE_URL = "https://fpjuanavqjfpcmjmapjp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwanVhbmF2cWpmcGNtam1hcGpwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTQ4NTU3OSwiZXhwIjoyMDk3MDYxNTc5fQ.BUoe9eEVV6LD0wbKOfxk_o7_m66b3W64BMaqWNS0KfA"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= RUTAS DE PRODUCTOS PRINCIPALES =================

@router.post("/api/products")
async def create_product(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(...),
    category_id: Optional[int] = Form(None),
    has_physical_stock: str = Form("true"),
    db: Session = Depends(get_db),
    admin_user: str = Depends(get_current_admin)
):
    try:
        file_bytes = await image.read()
        safe_filename = image.filename.replace(" ", "_")
        file_name = f"prod_{int(time.time())}_{safe_filename}" 
        
        supabase.storage.from_("productos-imagenes").upload(
            path=file_name, file=file_bytes, file_options={"content-type": image.content_type, "upsert": "true"}
        )
        public_url = supabase.storage.from_("productos-imagenes").get_public_url(file_name)
        
        new_product = Product(
            title=title, description=description, price=price, stock=stock,
            image_url=public_url, category_id=category_id,
            has_physical_stock=(has_physical_stock.lower() == 'true')
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    except Exception as e:
        print(f"\n❌ ERROR DE SUPABASE: {str(e)}\n") 
        raise HTTPException(status_code=500, detail=f"Error al subir: {str(e)}")

@router.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    # Mapeamos los datos para incluir las variantes automáticamente
    result = []
    for p in products:
        prod_data = {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "image_url": p.image_url,
            "category_id": p.category_id,
            "has_physical_stock": p.has_physical_stock,
            "variants": [
                {"id": v.id, "color_name": v.color_name, "stock": v.stock, "image_url": v.image_url}
                for v in p.variants
            ]
        }
        result.append(prod_data)
    return result

@router.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Formateamos el producto individual
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "image_url": p.image_url,
        "category_id": p.category_id,
        "has_physical_stock": p.has_physical_stock,
        "variants": [
            {"id": v.id, "color_name": v.color_name, "stock": v.stock, "image_url": v.image_url}
            for v in p.variants
        ]
    }

@router.put("/api/products/{product_id}")
async def edit_product(
    product_id: int, title: str = Form(...), description: str = Form(...),
    price: float = Form(...), category_id: Optional[int] = Form(None),
    has_physical_stock: str = Form("true"), image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db), admin_user: str = Depends(get_current_admin)
):
    try:
        producto = db.query(Product).filter(Product.id == product_id).first()
        if not producto: raise HTTPException(status_code=404, detail="Producto no encontrado")

        producto.title = title
        producto.description = description
        producto.price = price
        producto.category_id = category_id
        producto.has_physical_stock = (has_physical_stock.lower() == 'true')

        if image and image.filename:
            file_bytes = await image.read()
            safe_filename = image.filename.replace(" ", "_")
            file_name = f"prod_{int(time.time())}_{safe_filename}" 
            supabase.storage.from_("productos-imagenes").upload(path=file_name, file=file_bytes, file_options={"content-type": image.content_type, "upsert": "true"})
            producto.image_url = supabase.storage.from_("productos-imagenes").get_public_url(file_name)

        db.commit()
        db.refresh(producto)
        return {"message": "Producto editado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al editar: {str(e)}")

# ================= RUTAS PARA VARIANTES (NUEVO) =================

@router.post("/api/products/{product_id}/variants")
async def add_variant(
    product_id: int,
    color_name: str = Form(...),
    stock: int = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: str = Depends(get_current_admin)
):
    try:
        producto = db.query(Product).filter(Product.id == product_id).first()
        if not producto: raise HTTPException(status_code=404, detail="Producto padre no encontrado")

        public_url = None
        # Si le suben una foto específica para este color, la procesamos
        if image and image.filename:
            file_bytes = await image.read()
            safe_filename = image.filename.replace(" ", "_")
            file_name = f"var_{int(time.time())}_{safe_filename}"
            supabase.storage.from_("productos-imagenes").upload(
                path=file_name, file=file_bytes, file_options={"content-type": image.content_type, "upsert": "true"}
            )
            public_url = supabase.storage.from_("productos-imagenes").get_public_url(file_name)

        new_variant = ProductVariant(
            product_id=product_id,
            color_name=color_name,
            stock=stock,
            image_url=public_url
        )
        db.add(new_variant)
        db.commit()
        db.refresh(new_variant)
        return new_variant
    except Exception as e:
        print(f"\n❌ ERROR SUBIENDO VARIANTE: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Error al crear variante: {str(e)}")

@router.delete("/api/products/variants/{variant_id}")
def delete_variant(variant_id: int, db: Session = Depends(get_db), admin_user: str = Depends(get_current_admin)):
    variante = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variante: raise HTTPException(status_code=404, detail="Variante no encontrada")
    
    db.delete(variante)
    db.commit()
    return {"message": "Variante eliminada correctamente"}

# ================= OTROS ENDPOINTS =================

class StockUpdate(BaseModel):
    stock: int

@router.put("/api/products/{product_id}/stock")
def update_stock(product_id: int, stock_data: StockUpdate, db: Session = Depends(get_db), admin_user: str = Depends(get_current_admin)):
    producto = db.query(Product).filter(Product.id == product_id).first()
    if not producto: raise HTTPException(status_code=404, detail="Producto no encontrado")
    producto.stock = stock_data.stock
    db.commit()
    return {"message": "Stock actualizado", "nuevo_stock": producto.stock}

class CategoryUpdate(BaseModel):
    category_id: Optional[int] = None

@router.put("/api/products/{product_id}/category")
def update_product_category(product_id: int, category_data: CategoryUpdate, db: Session = Depends(get_db), admin_user: str = Depends(get_current_admin)):
    producto = db.query(Product).filter(Product.id == product_id).first()
    if not producto: raise HTTPException(status_code=404, detail="Producto no encontrado")
    producto.category_id = category_data.category_id
    db.commit()
    return {"message": "Categoría actualizada"}

@router.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), admin_user: str = Depends(get_current_admin)):
    producto = db.query(Product).filter(Product.id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    # Opcional: Si tuviera variantes asignadas en la base de datos y no usas CASCADE, las borramos primero:
    # db.query(ProductVariant).filter(ProductVariant.product_id == product_id).delete()

    db.delete(producto)
    db.commit()
    return {"message": "Producto eliminado correctamente"}