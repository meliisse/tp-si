from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count
from decimal import Decimal
from apps.core.models import Client
from .models import Facture, Paiement
from .serializers import FactureSerializer, PaiementSerializer
from utils.calculators import calculate_tva, calculate_total_with_tva

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.select_related('client').prefetch_related('expeditions', 'paiements')
    serializer_class = FactureSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client', 'est_payee', 'date_emission', 'mode']
    search_fields = ['client__nom', 'client__prenom', 'expeditions__numero']
    ordering_fields = ['date_emission', 'montant_ht', 'montant_ttc']
    ordering = ['-date_emission']

    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        facture = self.get_object()
        if facture.est_payee:
            return Response({'error': 'Invoice is already paid'}, status=status.HTTP_400_BAD_REQUEST)

        facture.est_payee = True
        facture.save()
        serializer = self.get_serializer(facture)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def payment_history(self, request, pk=None):
        facture = self.get_object()
        paiements = facture.paiements.all().order_by('-date_paiement')
        serializer = PaiementSerializer(paiements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        from utils.pdf_generator import generate_invoice_pdf
        facture = self.get_object()
        pdf_buffer = generate_invoice_pdf(facture)
        response = Response(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{facture.id}.pdf"'
        return response

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = Facture.objects.aggregate(
            total_invoices=Count('id'),
            total_amount_ht=Sum('montant_ht'),
            total_amount_ttc=Sum('montant_ttc'),
            paid_invoices=Count('id', filter=Q(est_payee=True)),
            unpaid_invoices=Count('id', filter=Q(est_payee=False))
        )
        return Response(stats)

class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.select_related('facture__client')
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['facture', 'mode', 'date_paiement']
    search_fields = ['facture__client__nom', 'facture__client__prenom', 'reference']
    ordering_fields = ['date_paiement', 'montant']
    ordering = ['-date_paiement']

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        montant_raw = data.get('montant')
        if montant_raw is None:
            return Response({'error': 'montant is required'}, status=status.HTTP_400_BAD_REQUEST)

        montant = Decimal(str(montant_raw))
        facture_id = data.get('facture')
        client_id = data.get('client')
        facture = None

        if facture_id:
            facture = Facture.objects.filter(id=facture_id).first()

        if not facture and client_id:
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

            montant_ht = (montant / Decimal('1.20')).quantize(Decimal('0.01'))
            montant_tva = (montant - montant_ht).quantize(Decimal('0.01'))
            facture = Facture.objects.create(
                client=client,
                montant_ht=montant_ht,
                montant_tva=montant_tva,
                montant_ttc=montant,
                est_payee=False
            )

        if not facture:
            return Response({'error': 'facture or client is required'}, status=status.HTTP_400_BAD_REQUEST)

        mode = data.get('methode') or data.get('mode') or 'especes'
        if mode == 'paypal':
            mode = 'virement'

        payload = {
            'facture': facture.id,
            'montant': montant,
            'mode': mode,
            'reference': data.get('reference', '')
        }

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        facture_id = request.data.get('facture_id')
        montant = Decimal(request.data.get('montant'))
        mode = request.data.get('mode')

        try:
            facture = Facture.objects.get(id=facture_id)
            if facture.est_payee:
                return Response({'error': 'Invoice is already fully paid'}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate remaining amount
            paid_amount = facture.paiements.aggregate(total=Sum('montant'))['total'] or 0
            remaining = facture.montant_ttc - paid_amount

            if montant > remaining:
                return Response({'error': f'Payment amount exceeds remaining balance of {remaining}'}, status=status.HTTP_400_BAD_REQUEST)

            paiement = Paiement.objects.create(
                facture=facture,
                montant=montant,
                mode=mode,
                reference=request.data.get('reference', '')
            )

            # Check if fully paid
            new_paid_total = paid_amount + montant
            if new_paid_total >= facture.montant_ttc:
                facture.est_payee = True
                facture.save()

            serializer = self.get_serializer(paiement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Facture.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
