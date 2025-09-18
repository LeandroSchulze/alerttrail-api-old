# app/routes/webhooks.py
from fastapi import APIRouter, Request, HTTPException
from app.billing.service import create_invoice_for_payment

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/mpago")
async def mpago_webhook(req: Request):
    payload = await req.json()
    status = payload.get("data", {}).get("status") or payload.get("status")
    if status not in ("approved","accredited"):
        return {"ok": True, "skipped": True}

    invoice = create_invoice_for_payment(payload)
    if not invoice.ok:
        # log y reintento asincrónico
        raise HTTPException(status_code=502, detail="Billing provider error")
    # guardar en DB: cae, pdf_url, number
    return {"ok": True, "cae": invoice.cae, "pdf": invoice.pdf_url, "n": invoice.number}
