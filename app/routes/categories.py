from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category
from pydantic import BaseModel

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