from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import UserCreate, UserOut, LoginRequest, Token
from ..models import User
from ..utils.security import verify_password, get_password_hash, create_access_token, issue_access_cookie, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# -------- JSON APIs (para clientes)
@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user = User(email=user_in.email, name=user_in.name, hashed_password=get_password_hash(user_in.password))
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    token = create_access_token(subject=user.email.lower())
    return {"access_token": token, "token_type": "bearer"}

# -------- HTML login (para navegador)
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
def login_web(response: Response, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    issue_access_cookie(response, subject=user.email.lower())
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout", include_in_schema=False)
def logout():
    r = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    r.delete_cookie("access_token", path="/")
    return r

@router.get("/me", response_model=UserOut)
def me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserOut(id=user.id, email=user.email, name=user.name, is_pro=user.is_pro)
