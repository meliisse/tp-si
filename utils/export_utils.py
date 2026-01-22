"""
Export and Print utilities for main tables
Supports CSV, Excel, and PDF exports
"""
import csv
import io
from datetime import datetime
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class ExportMixin:
    """Mixin to add export functionality to ViewSets"""
    
    def export_to_csv(self, queryset, fields, filename):
        """Export queryset to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        headers = [field.replace('_', ' ').title() for field in fields]
        writer.writerow(headers)
        
        # Write data
        for obj in queryset:
            row = []
            for field in fields:
                value = getattr(obj, field, '')
                if hasattr(value, 'all'):  # ManyToMany field
                    value = ', '.join(str(v) for v in value.all())
                row.append(str(value))
            writer.writerow(row)
        
        return response
    
    def export_to_pdf(self, queryset, fields, title, filename):
        """Export queryset to PDF"""
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Add title
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Prepare table data
        headers = [field.replace('_', ' ').title() for field in fields]
        data = [headers]
        
        for obj in queryset:
            row = []
            for field in fields:
                value = getattr(obj, field, '')
                if hasattr(value, 'all'):  # ManyToMany field
                    value = ', '.join(str(v) for v in value.all())
                row.append(str(value)[:50])  # Limit length for PDF
            data.append(row)
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response


def get_export_fields(model_name):
    """Get fields to export for each model"""
    fields_map = {
        'client': ['id', 'nom', 'prenom', 'email', 'telephone', 'adresse', 'solde', 'date_inscription', 'is_active'],
        'chauffeur': ['id', 'nom', 'prenom', 'numero_permis', 'telephone', 'disponibilite', 'date_embauche', 'is_active'],
        'vehicule': ['id', 'immatriculation', 'type', 'capacite', 'consommation', 'etat', 'is_active'],
        'destination': ['id', 'ville', 'pays', 'zone_geographique', 'tarif_base', 'is_active'],
        'typeservice': ['id', 'nom', 'description', 'is_active'],
        'tarification': ['id', 'type_service', 'destination', 'tarif_poids', 'tarif_volume', 'is_active'],
        'expedition': ['id', 'numero', 'client', 'type_service', 'destination', 'poids', 'volume', 'montant', 'statut', 'date_creation'],
        'tournee': ['id', 'date', 'chauffeur', 'vehicule', 'kilometrage', 'duree', 'consommation'],
    }
    return fields_map.get(model_name.lower(), [])


def get_model_title(model_name):
    """Get display title for model"""
    titles = {
        'client': 'Liste des Clients',
        'chauffeur': 'Liste des Chauffeurs',
        'vehicule': 'Liste des Véhicules',
        'destination': 'Liste des Destinations',
        'typeservice': 'Liste des Types de Service',
        'tarification': 'Liste des Tarifications',
        'expedition': 'Liste des Expéditions',
        'tournee': 'Liste des Tournées',
    }
    return titles.get(model_name.lower(), model_name.title())
