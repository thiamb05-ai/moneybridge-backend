from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Transaction
from wallets.models import Wallet
from decimal import Decimal

FIXED_FEE = Decimal('1.00')
EXCHANGE_MARGIN = Decimal('0.008')

RATES = {
    'EUR_XOF': Decimal('655.957') * (1 - EXCHANGE_MARGIN),
    'XOF_EUR': (1 / Decimal('655.957')) * (1 - EXCHANGE_MARGIN),
    'EUR_GHS': Decimal('16.5') * (1 - EXCHANGE_MARGIN),
    'GHS_EUR': (1 / Decimal('16.5')) * (1 - EXCHANGE_MARGIN),
}

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
    fee = FIXED_FEE
    total = amount + fee
    xof_amount = round(amount * RATES['EUR_XOF'], 0)
    return Response({
        'amount': str(amount),
        'fee': str(fee),
        'total': str(total),
        'xof_amount': str(xof_amount),
        'rate_eur_xof': str(round(RATES['EUR_XOF'], 2)),
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
        return Response({'error': 'Telephone requis'}, status=400)

    fee = FIXED_FEE
    total = amount + fee
    xof_amount = round(amount * RATES['EUR_XOF'], 0)

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
        description=f'Envoi {xof_amount} XOF a {recipient_name} via {method.upper()} ({country})',
    )

    return Response({
        'success': True,
        'transaction_id': str(tx.id),
        'amount': str(amount),
        'fee': str(fee),
        'total': str(total),
        'xof_amount': str(xof_amount),
        'recipient': recipient_name,
        'method': method,
        'status': 'completed',
        'message': f'{xof_amount} XOF envoyes a {recipient_name} via {method.upper()}',
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
        'message': f'{amount} EUR recu de {sender_name}',
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

    fee = Decimal('0.00')
    total = amount

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
        description=f'Virement vers {owner_name} - {iban[:8]}...',
    )

    return Response({
        'success': True,
        'transaction_id': str(tx.id),
        'amount': str(amount),
        'fee': '0.00',
        'total': str(total),
        'iban': iban,
        'status': 'completed',
        'message': f'Virement de {amount} EUR vers votre compte bancaire effectue instantanement',
        'new_balance': str(wallet.balance),
        'delay': 'Instantane',
    })
