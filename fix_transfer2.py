views = '''from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Transaction
from wallets.models import Wallet
from decimal import Decimal
import uuid

FEE_RATE = Decimal('0.02')
MIN_FEE = Decimal('1.00')

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_transactions(request):
    txs = Transaction.objects.filter(user=request.user).order_by('-created_at')[:20]
    data = []
    for t in txs:
        data.append({
            'id': t.id,
            'type': getattr(t, 'transaction_type', 'send'),
            'amount': str(t.amount),
            'status': t.status,
            'created_at': t.created_at,
            'description': getattr(t, 'description', ''),
        })
    return Response(data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def calculate_fee(request):
    try:
        amount = Decimal(str(request.data.get('amount', 0)))
    except:
        return Response({'error': 'Montant invalide'}, status=400)
    if amount <= 0:
        return Response({'error': 'Montant invalide'}, status=400)
    fee = max(amount * FEE_RATE, MIN_FEE)
    total = amount + fee
    return Response({
        'amount': str(amount),
        'fee': str(round(fee, 2)),
        'total': str(round(total, 2)),
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_money(request):
    try:
        amount = Decimal(str(request.data.get('amount', 0)))
    except:
        return Response({'error': 'Montant invalide'}, status=400)

    method = request.data.get('method', 'wave')
    recipient_name = request.data.get('recipient_name', '')
    recipient_phone = request.data.get('recipient_phone', '')
    country = request.data.get('country', 'SN')

    if amount <= 0:
        return Response({'error': 'Montant invalide'}, status=400)
    if not recipient_name:
        return Response({'error': 'Nom du beneficiaire requis'}, status=400)
    if not recipient_phone:
        return Response({'error': 'Telephone du beneficiaire requis'}, status=400)

    fee = max(amount * FEE_RATE, MIN_FEE)
    total = amount + fee

    try:
        wallet = Wallet.objects.get(user=request.user)
        if Decimal(str(wallet.balance)) < total:
            return Response({'error': 'Solde insuffisant'}, status=400)
        wallet.balance = Decimal(str(wallet.balance)) - total
        wallet.save()
    except Wallet.DoesNotExist:
        return Response({'error': 'Portefeuille introuvable'}, status=400)

    tx = Transaction.objects.create(
        user=request.user,
        amount=amount,
        status='completed',
        transaction_type='send',
        description=f'Envoi vers {recipient_name} via {method.upper()} ({country})',
    )

    return Response({
        'success': True,
        'transaction_id': str(tx.id),
        'amount': str(amount),
        'fee': str(round(fee, 2)),
        'total': str(round(total, 2)),
        'recipient': recipient_name,
        'method': method,
        'status': 'completed',
        'message': f'Transfert de {amount}€ envoye a {recipient_name} via {method.upper()}',
        'new_balance': str(wallet.balance),
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def receive_money(request):
    amount = Decimal(str(request.data.get('amount', 50)))
    method = request.data.get('method', 'wave')
    sender_name = request.data.get('sender_name', 'Expediteur')

    try:
        wallet = Wallet.objects.get(user=request.user)
        wallet.balance = Decimal(str(wallet.balance)) + amount
        wallet.save()
    except Wallet.DoesNotExist:
        return Response({'error': 'Portefeuille introuvable'}, status=400)

    tx = Transaction.objects.create(
        user=request.user,
        amount=amount,
        status='completed',
        transaction_type='receive',
        description=f'Recu de {sender_name} via {method.upper()}',
    )

    return Response({
        'success': True,
        'transaction_id': str(tx.id),
        'amount': str(amount),
        'new_balance': str(wallet.balance),
        'message': f'{amount}€ recu de {sender_name}',
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def withdraw_to_bank(request):
    try:
        amount = Decimal(str(request.data.get('amount', 0)))
    except:
        return Response({'error': 'Montant invalide'}, status=400)

    iban = request.data.get('iban', '')
    owner_name = request.data.get('owner_name', '')

    if amount <= 0:
        return Response({'error': 'Montant invalide'}, status=400)
    if not iban:
        return Response({'error': 'IBAN requis'}, status=400)
    if not owner_name:
        return Response({'error': 'Nom du titulaire requis'}, status=400)

    fee = max(amount * FEE_RATE, MIN_FEE)
    total = amount + fee

    try:
        wallet = Wallet.objects.get(user=request.user)
        if Decimal(str(wallet.balance)) < total:
            return Response({'error': 'Solde insuffisant'}, status=400)
        wallet.balance = Decimal(str(wallet.balance)) - total
        wallet.save()
    except Wallet.DoesNotExist:
        return Response({'error': 'Portefeuille introuvable'}, status=400)

    tx = Transaction.objects.create(
        user=request.user,
        amount=amount,
        status='completed',
        transaction_type='withdrawal',
        description=f'Virement vers {owner_name} - IBAN: {iban[:8]}...',
    )

    return Response({
        'success': True,
        'transaction_id': str(tx.id),
        'amount': str(amount),
        'fee': str(round(fee, 2)),
        'total': str(round(total, 2)),
        'iban': iban,
        'status': 'completed',
        'message': f'Virement de {amount}€ vers votre compte bancaire initie',
        'new_balance': str(wallet.balance),
        'delay': '1-3 jours ouvrables',
    })
'''

with open('transactions/views.py', 'w') as f:
    f.write(views)
print('views.py OK')

urls = '''from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_transactions, name='list_transactions'),
    path('create/', views.send_money, name='send_money'),
    path('receive/', views.receive_money, name='receive_money'),
    path('withdraw/', views.withdraw_to_bank, name='withdraw'),
    path('fee/', views.calculate_fee, name='calculate_fee'),
]
'''

with open('transactions/urls.py', 'w') as f:
    f.write(urls)
print('urls.py OK')