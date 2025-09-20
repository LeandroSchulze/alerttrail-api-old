# app/routes/auth.py
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..schemas import UserCreate, UserOut, LoginRequest, Token
from ..models import User
from ..utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    issue_access_cookie,
    decode_access_token,
)
from ..config import settings  # <-- para borrar cookie con dominio si aplica

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------- Helpers ----------------
def _get_user_pwd(u: User) -> str:
    """Devuelve el hash de password sin importar el nombre del campo."""
    return getattr(u, "hashed_password", None) or getattr(u, "password_hash", "") or ""

def _norm_email(e: str) -> str:
    return (e or "").strip().lower()

# ---------------- JSON APIs (para clientes) ----------------
@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    email_norm = _norm_email(user_in.email)
    exists = (
        db.query(User)
        .filter(func.lower(User.email) == email_norm)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user = User(email=email_norm, name=user_in.name or "")
    pwd_hash = get_password_hash(user_in.password)
    # Guardamos en ambos campos si están presentes en el modelo
    if hasattr(user, "hashed_password"):
        user.hashed_password = pwd_hash
    if hasattr(user, "password_hash"):
        user.password_hash = pwd_hash

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email_norm = _norm_email(payload.email)
    user = (
        db.query(User)
        .filter(func.lower(User.email) == email_norm)
        .first()
    )
    if not user or not verify_password(payload.password, _get_user_pwd(user)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    token = create_access_token(subject=user.email.lower())
    return {"access_token": token, "token_type": "bearer"}

# ---------------- HTML login (para navegador) ----------------
@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page():
    html = """<!doctype html><meta charset='utf-8'>
    <div style="font-family:system-ui;padding:24px;max-width:360px;margin:auto">
      <h1>Iniciar sesión</h1>
      <form method="post" action="/auth/login/web" style="display:grid;gap:10px">
        <input name="email" type="email" placeholder="Email" required>
        <input name="password" type="password" placeholder="Contraseña" required>
        <button>Entrar</button>
      </form>
      <p style="margin-top:10px"><a href="/">Volver</a></p>
    </div>"""
    return HTMLResponse(html)

@router.post("/login/web", include_in_schema=False)
def login_web(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email_norm = _norm_email(email)
    user = (
        db.query(User)
        .filter(func.lower(User.email) == email_norm)
        .first()
    )
    if not user or not verify_password(password, _get_user_pwd(user)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas.")
    issue_access_cookie(response, subject=user.email.lower())
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout", include_in_schema=False)
def logout():
    r = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    # borrar cookie sin dominio
    r.delete_cookie("access_token", path="/")
    # y también con dominio si lo estás usando (p.ej. .alerttrail.com)
    if getattr(settings, "COOKIE_DOMAIN", None):
        r.delete_cookie("access_token", path="/", domain=settings.COOKIE_DOMAIN)
    return r

# helper para limpiar cookie rápido
@router.get("/clear", include_in_schema=False)
def clear_cookie():
    r = HTMLResponse("ok")
    r.delete_cookie("access_token", path="/")
    if getattr(settings, "COOKIE_DOMAIN", None):
        r.delete_cookie("access_token", path="/", domain=settings.COOKIE_DOMAIN)
    return r

@router.get("/me", response_model=UserOut)
def me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(func.lower(User.email) == _norm_email(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserOut(id=user.id, email=user.email, name=user.name, is_pro=getattr(user, "is_pro", False))

# ---------------- Emergencia: reset/crear admin desde ENV ----------------
@router.post("/_force_admin_reset", include_in_schema=True)
def _force_admin_reset(
    secret: str = Query(..., description="Debe coincidir con ADMIN_SETUP_SECRET (o SECRET_KEY)"),
    db: Session = Depends(get_db),
):
    """
    Crea/actualiza el admin usando variables de entorno:
      ADMIN_EMAIL, ADMIN_PASS, ADMIN_NAME
    Protegido por ADMIN_SETUP_SECRET (o SECRET_KEY si no está el primero).
    """
    setup_secret = os.getenv("ADMIN_SETUP_SECRET") or os.getenv("SECRET_KEY") or ""
    if not setup_secret or secret != setup_secret:
        raise HTTPException(status_code=403, detail="forbidden")

    email = _norm_email(os.getenv("ADMIN_EMAIL", ""))
    password = os.getenv("ADMIN_PASS", "")
    name = os.getenv("ADMIN_NAME", "Admin")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Faltan ADMIN_EMAIL o ADMIN_PASS")

    pwd_hash = get_password_hash(password)
    user = (
        db.query(User)
        .filter(func.lower(User.email) == email)
        .first()
    )
    if user:
        if hasattr(user, "hashed_password"):
            user.hashed_password = pwd_hash
        if hasattr(user, "password_hash"):
            user.password_hash = pwd_hash
        if hasattr(user, "name") and not user.name:
            user.name = name
        action = "actualizado"
    else:
        user = User(email=email, name=name)
        if hasattr(user, "hashed_password"):
            user.hashed_password = pwd_hash
        if hasattr(user, "password_hash"):
            user.password_hash = pwd_hash
        db.add(user)
        action = "creado"

    db.commit()
    return {"ok": True, "admin": email, "action": action}
