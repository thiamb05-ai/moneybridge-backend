views = '''from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Transaction

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_transactions(request):
    transactions = Transaction.objects.filter(user=request.user).order_by("-created_at")[:20]
    data = []
    for t in transactions:
        data.append({
            "id": t.id,
            "type": t.transaction_type,
            "amount": str(t.amount),
            "currency": t.currency,
            "status": t.status,
            "created_at": t.created_at,
        })
    return Response(data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    amount = request.data.get("amount")
    currency = request.data.get("currency", "EUR")
    transaction_type = request.data.get("type")
    t = Transaction.objects.create(
        user=request.user,
        amount=amount,
        currency=currency,
        transaction_type=transaction_type,
        status="pending"
    )
    return Response({"id": t.id, "status": t.status})
'''

urls = '''from django.urls import path
from . import views

urlpatterns = [
    path("", views.my_transactions, name="my-transactions"),
    path("create/", views.create_transaction, name="create-transaction"),
]
'''

with open('transactions/views.py', 'w') as f:
    f.write(views)
print('transactions/views.py OK')

with open('transactions/urls.py', 'w') as f:
    f.write(urls)
print('transactions/urls.py OK')