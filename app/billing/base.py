# app/billing/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class InvoiceItem:
    description: str
    quantity: float
    unit_price: float
    currency: str = "ARS"

@dataclass
class InvoiceRequest:
    customer_email: str
    customer_name: str
    doc_type: str = "DNI"     # o "CUIT"
    doc_number: str = ""      # opcional
    items: list[InvoiceItem] = None

@dataclass
class InvoiceResponse:
    ok: bool
    cae: str | None
    pdf_url: str | None
    number: str | None
    raw: dict | None

class BillingProvider(ABC):
    @abstractmethod
    def create_invoice(self, data: InvoiceRequest) -> InvoiceResponse: ...
