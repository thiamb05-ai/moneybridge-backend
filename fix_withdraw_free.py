content = open('transactions/views.py').read()

old = '''    fee = FIXED_FEE
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
        description=f'Virement vers {owner_name} - {iban[:8]}...',
    )

    return Response({
        'success': True,
        'transaction_id': str(tx.id),
        'amount': str(amount),
        'fee': str(fee),
        'total': str(total),
        'iban': iban,
        'status': 'completed',
        'message': f'Virement de {amount} EUR vers votre compte bancaire effectue',
        'new_balance': str(wallet.balance),
        'delay': 'Instantane',
    })'''

new = '''    fee = Decimal('0.00')
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
    })'''

content = content.replace(old, new)
with open('transactions/views.py', 'w') as f:
    f.write(content)
print('OK !')