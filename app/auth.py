from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from .database import get_db
from .models import User
from .utils.security import ALGORITHM, decode_access_token, get_token_from_cookie
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def _cred_exc():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def get_current_user(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    # 1) Cookie
    cookie_token = get_token_from_cookie(request)
    if cookie_token:
        payload = decode_access_token(cookie_token)
        if payload and payload.get("sub"):
            user = db.query(User).filter(User.email == payload["sub"]).first()
            if user:
                return user
    # 2) Bearer
    if not token:
        raise _cred_exc()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise _cred_exc()
    except JWTError:
        raise _cred_exc()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise _cred_exc()
    return user
