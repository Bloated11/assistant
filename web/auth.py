from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import OAuth2PasswordBearer
from web.database import get_db, User

SECRET_KEY = "phenom_ai_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login", auto_error=False)

def verify_password(username: str, password: str, db = None) -> Optional[dict]:
    if db is None:
        db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user:
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        if hashed_input == user.hashed_password:
            return {"id": user.id, "username": user.username, "email": user.email}
    return None

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Optional[str] = Cookie(None, alias="access_token"), db = None) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        if db is None:
            db = next(get_db())
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {"id": user.id, "username": user.username, "email": user.email}
    except JWTError:
        return None
    return None
