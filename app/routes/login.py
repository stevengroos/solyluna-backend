from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AdminUser
from app.auth import verificar_password, crear_token_acceso

router = APIRouter()

@router.post("/api/token")
def login_admin(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db) # <-- Conectamos con la base de datos
):
    # 1. Buscamos al usuario real en la base de datos de Supabase
    admin = db.query(AdminUser).filter(AdminUser.username == form_data.username).first()
    
    # 2. Si el usuario no existe, rechazamos
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales incorrectas" # Mensaje genérico por seguridad
        )
    
    # 3. Comparamos la contraseña que escribió con el Hash encriptado de la BD
    if not verificar_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credenciales incorrectas"
        )
    
    # 4. Si todo está perfecto, le damos su pase VIP (Token JWT)
    access_token = crear_token_acceso(data={"sub": admin.username})
    
    return {"access_token": access_token, "token_type": "bearer"}