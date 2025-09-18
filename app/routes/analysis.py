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
    input_summary = (data.content or "")[:280]
    result = {"summary_length": len(input_summary), "title_length": len(data.title)}
    row = Analysis(user_id=user.id, title=data.title, input_summary=input_summary, result_json=json.dumps(result))
    db.add(row); db.commit(); db.refresh(row)
    return AnalysisOut(id=row.id, title=row.title, input_summary=row.input_summary, result_json=result)

@router.get("/{analysis_id}/pdf")
def analysis_pdf(analysis_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
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
    return [AnalysisOut(id=r.id, title=r.title, input_summary=r.input_summary, result_json=json.loads(r.result_json)) for r in rows]
