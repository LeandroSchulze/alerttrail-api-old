
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
import json
from pathlib import Path
from datetime import datetime, timedelta

router = APIRouter()
SECRET_KEY = "alerttrail-secret"
ALGORITHM = "HS256"
USERS_FILE = Path(__file__).resolve().parent.parent / "data" / "users.json"

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def authenticate_user(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == password:
            return user
    return None

def create_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(hours=12)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_token({"sub": user["username"], "plan": user["plan"]})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register")
def register(form_data: OAuth2PasswordRequestForm = Depends()):
    users = load_users()
    for user in users:
        if user["username"] == form_data.username:
            raise HTTPException(status_code=400, detail="Usuario ya existe")
    users.append({
        "username": form_data.username,
        "password": form_data.password,
        "plan": "free"
    })
    save_users(users)
    return {"message": "Registro exitoso"}
