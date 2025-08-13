# AlertTrail API (FastAPI)

Backend listo para desplegar (Render/Railway) y subir a GitHub.
Incluye:
- FastAPI + JWT (login/registro), SQLite con SQLAlchemy
- Endpoints de análisis (dummy) y generación de PDF (placeholder)
- Estructura de rutas estable (sin errores de imports)
- Soporte para CORS, .env, Dockerfile, render.yaml

## Ejecutar local
```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # o definí tus valores
uvicorn app.main:app --reload
```

## Variables de entorno
Ver `.env.example`.

## Despliegue en Render
- Conectá el repo y seleccioná: `uvicorn app.main:app --host=0.0.0.0 --port=10000`
- O usá `render.yaml` del repo.
