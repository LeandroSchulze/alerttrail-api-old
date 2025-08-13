from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

def build_analysis_pdf(title: str, content: str, result: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"AlertTrail - Reporte de Análisis")
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Título: {title}")
    y -= 20
    c.drawString(50, y, "Resumen de entrada:")
    y -= 14
    for line in (content[:1000].splitlines() or ["(sin contenido)"]):
        c.drawString(60, y, line[:100])
        y -= 14
        if y < 80:
            c.showPage()
            y = h - 50
    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
