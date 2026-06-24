from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category
from pydantic import BaseModel
from app.auth import get_current_admin
from app.models import Product

router = APIRouter()

class CategoryCreate(BaseModel):
    name: str

@router.get("/api/categories")
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

@router.post("/api/categories")
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # Validar si ya existe
    db_category = db.query(Category).filter(Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="La categoría ya existe")
    
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


class CategoryUpdate(BaseModel):
    name: str

@router.put("/api/categories/{category_id}")
def update_category(category_id: int, category_data: CategoryUpdate, db: Session = Depends(get_db), admin_user: str = Depends(get_current_admin)):
    categoria = db.query(Category).filter(Category.id == category_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Validar que el nuevo nombre no exista ya en otra categoría
    existe = db.query(Category).filter(Category.name == category_data.name, Category.id != category_id).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe otra categoría con ese nombre")
        
    categoria.name = category_data.name
    db.commit()
    db.refresh(categoria)
    return categoria

@router.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), admin_user: str = Depends(get_current_admin)):
    categoria = db.query(Category).filter(Category.id == category_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # IMPORTANTE: Desvincular los productos asociados a esta categoría antes de borrarla
    db.query(Product).filter(Product.category_id == category_id).update({Product.category_id: None})
    
    db.delete(categoria)
    db.commit()
    return {"message": "Categoría eliminada correctamente y productos desvinculados"}