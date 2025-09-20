from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute

from .config import settings
from .database import Base, engine
from .routes import auth as auth_routes
from .routes import analysis as analysis_routes

# Crear tablas en el arranque (simple para MVP)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AlertTrail API", version="1.0.0")

# CORS
if settings.CORS_ORIGINS == "*":
    allow_origins = ["*"]
elif isinstance(settings.CORS_ORIGINS, list):
    allow_origins = [str(x) for x in settings.CORS_ORIGINS]
else:
    allow_origins = [str(settings.CORS_ORIGINS)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(auth_routes.router)
app.include_router(analysis_routes.router)

# Aliases útiles
@app.get("/logout", include_in_schema=False)
def logout_alias():
    return RedirectResponse(url="/auth/logout", status_code=307)

@app.get("/login", include_in_schema=False)
def login_alias():
    return RedirectResponse(url="/auth/login", status_code=307)

@app.get("/", tags=["root"])
def root():
    return {"name": "AlertTrail API", "status": "ok"}

@app.get("/health", tags=["root"])
def health():
    return {"ok": True}

# Log de rutas al arrancar (para ver que /auth/* está montado)
@app.on_event("startup")
def _log_routes():
    paths = sorted([r.path for r in app.routes if isinstance(r, APIRoute)])
    print("\n=== ROUTES ===")
    for p in paths:
        print(p)
    print("==============\n")
