# app/billing/service.py
from .base import InvoiceRequest, InvoiceItem
from .facturante import FacturanteProvider

provider = FacturanteProvider()

def create_invoice_for_payment(mp_payment: dict):
    # Mapear desde Mercado Pago
    email = mp_payment["payer"]["email"]
    name = mp_payment["payer"].get("first_name","") + " " + mp_payment["payer"].get("last_name","")
    items = [InvoiceItem(
        description=it["title"], quantity=it.get("quantity", 1), unit_price=float(it["unit_price"])
    ) for it in mp_payment.get("additional_info", {}).get("items", []) or [{
        "title": mp_payment["description"], "unit_price": mp_payment["transaction_amount"], "quantity": 1
    }]]

    req = InvoiceRequest(customer_email=email, customer_name=name.strip(), items=items)
    return provider.create_invoice(req)
