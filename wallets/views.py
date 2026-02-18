from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_wallet(request):
    try:
        from .models import Wallet
        wallet = Wallet.objects.get(user=request.user)
        return Response({
            "balance": str(wallet.balance),
            "currency": wallet.currency,
        })
    except Exception:
        return Response({"balance": "0.00", "currency": "EUR"})
