from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Facture

def generate_facture_pdf(facture: Facture):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{facture.id}.pdf"'
    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Facture n°{facture.id}")
    p.drawString(100, 780, f"Client: {facture.client}")
    p.drawString(100, 760, f"Date: {facture.date_emission}")
    p.drawString(100, 740, f"Montant HT: {facture.montant_ht} €")
    p.drawString(100, 720, f"TVA: {facture.montant_tva} €")
    p.drawString(100, 700, f"Montant TTC: {facture.montant_ttc} €")
    p.showPage()
    p.save()
    return response
