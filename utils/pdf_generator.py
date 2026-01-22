import os
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from apps.billing.models import Facture
from apps.logistics.models import Expedition, TrackingLog
from .calculators import TaxCalculator

class PDFGenerator:
    """PDF generator for invoices and tracking documents"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )

        self.company_style = ParagraphStyle(
            'CompanyStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            alignment=1
        )

        self.address_style = ParagraphStyle(
            'AddressStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=1
        )

    def generate_invoice_pdf(self, facture):
        """
        Generate PDF invoice for a given Facture instance
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        # Company header
        elements.extend(self._create_invoice_header(facture))

        # Invoice details
        elements.extend(self._create_invoice_details(facture))

        # Expedition details table
        elements.extend(self._create_expedition_table(facture))

        # Totals section
        elements.extend(self._create_totals_section(facture))

        # Footer
        elements.extend(self._create_footer())

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_tracking_pdf(self, expedition):
        """
        Generate PDF tracking document for an expedition
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        # Header
        elements.extend(self._create_tracking_header(expedition))

        # Tracking details
        elements.extend(self._create_tracking_details(expedition))

        # Tracking history table
        elements.extend(self._create_tracking_history_table(expedition))

        # Footer
        elements.extend(self._create_footer())

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def _create_invoice_header(self, facture):
        """Create invoice header section"""
        elements = []

        # Company information
        elements.append(Paragraph("TRANSPORT MANAGER", self.company_style))
        elements.append(Paragraph("123 Logistics Street", self.address_style))
        elements.append(Paragraph("Paris, France 75001", self.address_style))
        elements.append(Paragraph("Phone: +33 1 23 45 67 89", self.address_style))
        elements.append(Spacer(1, 20))

        # Invoice title
        elements.append(Paragraph("INVOICE", self.title_style))
        elements.append(Spacer(1, 20))

        # Invoice info table
        invoice_data = [
            ['Invoice Number:', f'INV-{facture.id:06d}'],
            ['Invoice Date:', facture.date_creation.strftime('%d/%m/%Y')],
            ['Due Date:', (facture.date_creation + timezone.timedelta(days=30)).strftime('%d/%m/%Y')],
            ['Client:', f"{facture.client.nom} {facture.client.prenom}"],
            ['Client Address:', facture.client.adresse],
        ]

        table = Table(invoice_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_invoice_details(self, facture):
        """Create invoice details section"""
        elements = []

        # Period information
        period_text = f"Invoice for services provided from {facture.date_creation.strftime('%d/%m/%Y')} to {(facture.date_creation + timezone.timedelta(days=30)).strftime('%d/%m/%Y')}"
        elements.append(Paragraph(period_text, self.styles['Normal']))
        elements.append(Spacer(1, 20))

        return elements

    def _create_expedition_table(self, facture):
        """Create expedition details table"""
        elements = []

        # Table header
        elements.append(Paragraph("Expedition Details", self.styles['Heading2']))
        elements.append(Spacer(1, 10))

        # Table data
        data = [['Expedition #', 'Date', 'Destination', 'Weight (kg)', 'Volume (m³)', 'Amount (€)']]

        for expedition in facture.expeditions.all():
            data.append([
                expedition.numero,
                expedition.date_creation.strftime('%d/%m/%Y'),
                f"{expedition.destination.ville}, {expedition.destination.pays}",
                f"{expedition.poids}",
                f"{expedition.volume}",
                f"{expedition.montant:.2f}"
            ])

        table = Table(data, colWidths=[1.2*inch, 1*inch, 2*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_totals_section(self, facture):
        """Create totals section"""
        elements = []

        # Calculate totals
        subtotal = sum(exp.montant for exp in facture.expeditions.all())
        tax_info = TaxCalculator.calculate_tva(subtotal)

        totals_data = [
            ['Subtotal (HT):', f'{tax_info["amount_ht"]:.2f} €'],
            ['TVA (20%):', f'{tax_info["tva_amount"]:.2f} €'],
            ['Total (TTC):', f'{tax_info["total_ttc"]:.2f} €']
        ]

        table = Table(totals_data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 30))

        return elements

    def _create_tracking_header(self, expedition):
        """Create tracking document header"""
        elements = []

        # Company information
        elements.append(Paragraph("TRANSPORT MANAGER", self.company_style))
        elements.append(Paragraph("Tracking Document", self.title_style))
        elements.append(Spacer(1, 20))

        # Expedition info
        tracking_data = [
            ['Expedition Number:', expedition.numero],
            ['Client:', f"{expedition.client.nom} {expedition.client.prenom}"],
            ['Destination:', f"{expedition.destination.ville}, {expedition.destination.pays}"],
            ['Status:', expedition.get_statut_display()],
            ['Creation Date:', expedition.date_creation.strftime('%d/%m/%Y %H:%M')],
        ]

        if expedition.date_livraison:
            tracking_data.append(['Delivery Date:', expedition.date_livraison.strftime('%d/%m/%Y %H:%M')])

        table = Table(tracking_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_tracking_details(self, expedition):
        """Create tracking details section"""
        elements = []

        # Package details
        details_data = [
            ['Weight:', f"{expedition.poids} kg"],
            ['Volume:', f"{expedition.volume} m³"],
            ['Service Type:', expedition.type_service.nom],
            ['Amount:', f"{expedition.montant:.2f} €"],
        ]

        if expedition.description:
            details_data.append(['Description:', expedition.description])

        table = Table(details_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_tracking_history_table(self, expedition):
        """Create tracking history table"""
        elements = []

        elements.append(Paragraph("Tracking History", self.styles['Heading2']))
        elements.append(Spacer(1, 10))

        # Table data
        data = [['Date & Time', 'Location', 'Status', 'Comment', 'Driver']]

        for log in expedition.trackings.order_by('-date'):
            data.append([
                log.date.strftime('%d/%m/%Y %H:%M'),
                log.lieu,
                log.statut,
                log.commentaire or '',
                f"{log.chauffeur.nom} {log.chauffeur.prenom}" if log.chauffeur else ''
            ])

        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        return elements

    def _create_footer(self):
        """Create document footer"""
        elements = []

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for choosing Transport Manager!", self.styles['Normal']))
        elements.append(Paragraph("For any questions, please contact our support team.", self.styles['Normal']))

        return elements

# Utility functions for easy PDF generation
def generate_invoice_pdf(facture):
    """
    Convenience function to generate invoice PDF
    """
    generator = PDFGenerator()
    return generator.generate_invoice_pdf(facture)

def generate_tracking_pdf(expedition):
    """
    Convenience function to generate tracking PDF
    """
    generator = PDFGenerator()
    return generator.generate_tracking_pdf(expedition)
