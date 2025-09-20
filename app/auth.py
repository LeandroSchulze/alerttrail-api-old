# app/auth.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import JWTError, jwt

from .database import get_db
from .models import User
from .utils.security import ALGORITHM, decode_access_token, get_token_from_cookie
from .config import settings

# IMPORTANTE: no dispares 401 automático si falta el Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def _cred_exc():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

def _find_user_by_email(db: Session, email: str) -> User | None:
    if not email:
        return None
    return (
        db.query(User)
        .filter(func.lower(User.email) == email.strip().lower())
        .first()
    )

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> User:
    # 1) Cookie JWT
    cookie_token = get_token_from_cookie(request)
    if cookie_token:
        payload = decode_access_token(cookie_token)
        sub = payload.get("sub") if payload else None
        user = _find_user_by_email(db, sub or "")
        if user:
            return user

    # 2) Authorization: Bearer <token>
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            sub = payload.get("sub")
            user = _find_user_by_email(db, sub or "")
            if user:
                return user
        except JWTError:
            pass

    # Si ninguna via autenticó:
    raise _cred_exc()

# Útil para endpoints "opcionales" (no obligan a estar logueado)
def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> User | None:
    try:
        return get_current_user(request, db, token)
    except HTTPException:
        return None
