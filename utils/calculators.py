from decimal import Decimal
from apps.core.models import Tarification, Destination

def calculate_shipping_cost(type_service, destination, weight, volume):
    """
    Calculate the total shipping cost based on service type, destination, weight, and volume.

    Args:
        type_service: TypeService instance
        destination: Destination instance
        weight: Decimal - weight in kg
        volume: Decimal - volume in m3

    Returns:
        Decimal: Total cost including base tariff and weight/volume rates
    """
    try:
        tarification = Tarification.objects.get(
            type_service=type_service,
            destination=destination,
            is_active=True
        )

        # Calculate cost: base tariff + (weight * rate per kg) + (volume * rate per m3)
        base_cost = destination.tarif_base
        weight_cost = weight * tarification.tarif_poids
        volume_cost = volume * tarification.tarif_volume

        total_cost = base_cost + weight_cost + volume_cost

        return total_cost.quantize(Decimal('0.01'))  # Round to 2 decimal places

    except Tarification.DoesNotExist:
        raise ValueError(f"No pricing found for {type_service} to {destination}")

def calculate_tva(amount, tva_rate=0.20):
    """
    Calculate TVA (VAT) amount.

    Args:
        amount: Decimal - base amount
        tva_rate: float - TVA rate (default 20%)

    Returns:
        Decimal: TVA amount
    """
    return (amount * Decimal(str(tva_rate))).quantize(Decimal('0.01'))

def calculate_total_with_tva(amount_ht, tva_rate=0.20):
    """
    Calculate total amount including TVA.

    Args:
        amount_ht: Decimal - amount before tax
        tva_rate: float - TVA rate (default 20%)

    Returns:
        tuple: (tva_amount, total_ttc)
    """
    tva_amount = calculate_tva(amount_ht, tva_rate)
    total_ttc = amount_ht + tva_amount
    return tva_amount, total_ttc

def calculate_fuel_consumption(distance, consumption_rate):
    """
    Calculate fuel consumption for a trip.

    Args:
        distance: Decimal - distance in km
        consumption_rate: Decimal - consumption in L/100km

    Returns:
        Decimal: Fuel consumption in liters
    """
    return ((distance * consumption_rate) / 100).quantize(Decimal('0.01'))
