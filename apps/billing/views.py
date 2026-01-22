
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Facture
from .pdf_utils import generate_facture_pdf
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def facture_pdf(request, pk):
	facture = get_object_or_404(Facture, pk=pk)
	return generate_facture_pdf(facture)