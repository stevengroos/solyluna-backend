import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AdminUser

# Configuración secreta
SECRET_KEY = "SOL_Y_LUNA_SUPER_SECRET_KEY_98765"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

def verificar_password(plain_password: str, hashed_password: str):
    # Comparamos convirtiendo tanto la contraseña plana como el hash de la BD a bytes
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def crear_token_acceso(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # 1. Desencriptamos el Token para ver quién es el usuario
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
            
        # 2. Verificamos que el usuario siga existiendo realmente en la base de datos de Supabase
        admin = db.query(AdminUser).filter(AdminUser.username == username).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El usuario ya no existe en el sistema",
            )
            
        return username
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )