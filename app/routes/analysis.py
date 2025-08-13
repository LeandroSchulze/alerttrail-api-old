from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import AnalysisCreate, AnalysisOut
from ..models import Analysis
from ..auth import get_current_user
from ..utils.pdf import build_analysis_pdf
from fastapi.responses import StreamingResponse
import json
from io import BytesIO

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("", response_model=AnalysisOut)
def run_analysis(data: AnalysisCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Demo/dummy analysis (reemplazar con lógica real)
    result = {
        "status": "ok",
        "findings": [
            {"type": "failed_login", "count": 3},
            {"type": "suspicious_ip", "value": "203.0.113.45"}
        ]
    }
    analysis = Analysis(
        user_id=user.id,
        title=data.title,
        input_summary=(data.content[:500] + ("..." if len(data.content) > 500 else "")),
        result_json=json.dumps(result, ensure_ascii=False)
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return AnalysisOut(
        id=analysis.id,
        title=analysis.title,
        input_summary=analysis.input_summary,
        result_json=result
    )

@router.get("/{analysis_id}/pdf")
def download_pdf(analysis_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    pdf_bytes = build_analysis_pdf(analysis.title, analysis.input_summary, json.loads(analysis.result_json))
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="alerttrail_analysis_{analysis_id}.pdf"'
    })

@router.get("", response_model=list[AnalysisOut])
def list_my_analyses(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.query(Analysis).filter(Analysis.user_id == user.id).order_by(Analysis.created_at.desc()).all()
    out = []
    for r in rows:
        out.append(AnalysisOut(id=r.id, title=r.title, input_summary=r.input_summary, result_json=json.loads(r.result_json)))
    return out
