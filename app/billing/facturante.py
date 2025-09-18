# app/billing/facturante.py
import os, requests
from .base import BillingProvider, InvoiceRequest, InvoiceResponse

FACT_API = "https://api.facturante.com/..."
FACT_API_KEY = os.getenv("FACT_API_KEY")
FACT_CUIT = os.getenv("FACT_CUIT")
FACT_PTO_VTA = os.getenv("FACT_PTO_VTA")

class FacturanteProvider(BillingProvider):
    def create_invoice(self, data: InvoiceRequest) -> InvoiceResponse:
        # Mapeo simple a Facturante (Factura C para Monotributo)
        payload = {
            "cuit": FACT_CUIT,
            "ptoVta": int(FACT_PTO_VTA),
            "tipoCmp": 11,               # 11 = Factura C
            "concepto": 1,               # Productos/servicios
            "docTipo": 99 if data.doc_type == "DNI" else 80,  # 99=DNI, 80=CUIT
            "docNro": int(data.doc_number or 0),
            "moneda": "PES",
            "monCotiz": 1.0,
            "cbteDesde": 0, "cbteHasta": 0,  # auto
            "items": [
                {"des": it.description, "qty": it.quantity, "imp": it.unit_price, "iva": 0}
                for it in (data.items or [])
            ],
            "cliente": {"email": data.customer_email, "nombre": data.customer_name},
        }
        r = requests.post(FACT_API, json=payload, headers={"Authorization": f"Bearer {FACT_API_KEY}"}, timeout=20)
        if r.ok:
            j = r.json()
            return InvoiceResponse(
                ok=True,
                cae=j.get("cae"),
                pdf_url=j.get("pdfUrl") or j.get("pdf"),
                number=str(j.get("cbteNro")),
                raw=j
            )
        return InvoiceResponse(ok=False, cae=None, pdf_url=None, number=None, raw={"status": r.status_code, "text": r.text})
