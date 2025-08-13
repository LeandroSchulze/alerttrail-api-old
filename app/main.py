from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from .routes import auth as auth_routes
from .routes import analysis as analysis_routes

# Crear tablas en el arranque (simple para MVP)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AlertTrail API", version="1.0.0")

# CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"] if settings.CORS_ORIGINS == "*" else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(auth_routes.router)
app.include_router(analysis_routes.router)

@app.get("/", tags=["root"])
def root():
    return {"name": "AlertTrail API", "status": "ok"}
