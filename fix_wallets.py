views = '''from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Wallet

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_wallet(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
        return Response({
            "balance": str(wallet.balance),
            "currency": wallet.currency,
        })
    except Wallet.DoesNotExist:
        return Response({"balance": "0.00", "currency": "EUR"})
'''

urls = '''from django.urls import path
from . import views

urlpatterns = [
    path("my-wallet/", views.my_wallet, name="my-wallet"),
]
'''

with open('wallets/views.py', 'w') as f:
    f.write(views)
print('wallets/views.py OK')

with open('wallets/urls.py', 'w') as f:
    f.write(urls)
print('wallets/urls.py OK')