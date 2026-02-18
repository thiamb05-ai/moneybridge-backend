"""
Transaction Service - Core business logic for handling transactions.
"""
from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
from transactions.models import Transaction, LedgerEntry, TransactionFee
from wallets.models import Wallet
from exchange.models import ExchangeRate, CurrencyConversion


class TransactionService:
    """Service for handling all transaction operations with double-entry ledger."""
    
    @staticmethod
    @db_transaction.atomic
    def create_receive_transaction(user, amount, currency, source_details):
        """
        Create a transaction for receiving money from mobile money.
        
        Args:
            user: User object
            amount: Amount in original currency (XOF, GHS, etc.)
            currency: Original currency code
            source_details: Dict with provider info (provider, phone_number, etc.)
        
        Returns:
            Transaction object
        """
        # Get or create wallet in EUR (target currency)
        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            currency='EUR'
        )
        
        # Get exchange rate
        exchange_rate = ExchangeRate.get_current_rate(currency, 'EUR')
        if not exchange_rate:
            raise ValueError(f"Exchange rate not found for {currency}/EUR")
        
        # Convert amount to EUR
        eur_amount = exchange_rate.convert(amount, direction='sell')
        eur_amount = Decimal(str(eur_amount)).quantize(Decimal('0.01'))
        
        # Calculate fee
        fee_config = TransactionFee.objects.filter(
            transaction_type='RECEIVE_MOBILE_MONEY',
            is_active=True
        ).first()
        
        fee_amount = fee_config.calculate_fee(eur_amount) if fee_config else Decimal('0.00')
        
        # Net amount to credit to user
        net_amount = eur_amount - fee_amount
        
        # Create transaction
        txn = Transaction.objects.create(
            user=user,
            transaction_type='RECEIVE_MOBILE_MONEY',
            status='PENDING',
            amount=net_amount,
            currency='EUR',
            original_amount=amount,
            original_currency=currency,
            exchange_rate=exchange_rate.sell_rate,
            fee_amount=fee_amount,
            fee_currency='EUR',
            destination_wallet=wallet,
            description=f"Received from {source_details.get('provider')}",
            metadata=source_details
        )
        
        # Create ledger entries (double-entry bookkeeping)
        # Credit user wallet with net amount
        LedgerEntry.objects.create(
            transaction=txn,
            entry_type='CREDIT',
            account_type='USER_WALLET',
            amount=net_amount,
            currency='EUR',
            wallet=wallet,
            balance_after=wallet.available_balance + net_amount,
            description=f"Credit from mobile money - {source_details.get('provider')}"
        )
        
        # If there's a fee, debit it
        if fee_amount > 0:
            LedgerEntry.objects.create(
                transaction=txn,
                entry_type='DEBIT',
                account_type='FEES',
                amount=fee_amount,
                currency='EUR',
                description=f"Transaction fee - {source_details.get('provider')}"
            )
            
            LedgerEntry.objects.create(
                transaction=txn,
                entry_type='CREDIT',
                account_type='REVENUE',
                amount=fee_amount,
                currency='EUR',
                description=f"Fee revenue from transaction {txn.id}"
            )
        
        return txn
    
    @staticmethod
    @db_transaction.atomic
    def complete_receive_transaction(transaction_obj):
        """
        Complete a pending receive transaction and update wallet balance.
        
        Args:
            transaction_obj: Transaction object to complete
        """
        if transaction_obj.status != 'PENDING':
            raise ValueError(f"Transaction is not pending: {transaction_obj.status}")
        
        # Update wallet balance
        wallet = transaction_obj.destination_wallet
        wallet.available_balance += transaction_obj.amount
        wallet.save()
        
        # Update transaction status
        transaction_obj.status = 'COMPLETED'
        transaction_obj.completed_at = timezone.now()
        transaction_obj.save()
        
        # Create currency conversion record if applicable
        if transaction_obj.original_currency and transaction_obj.original_currency != transaction_obj.currency:
            CurrencyConversion.objects.create(
                transaction=transaction_obj,
                from_currency=transaction_obj.original_currency,
                to_currency=transaction_obj.currency,
                from_amount=transaction_obj.original_amount,
                to_amount=transaction_obj.amount + transaction_obj.fee_amount,
                rate_applied=transaction_obj.exchange_rate
            )
    
    @staticmethod
    @db_transaction.atomic
    def create_bank_transfer_transaction(user, bank_account, amount, currency='EUR'):
        """
        Create a transaction for sending money to a bank account via SEPA.
        
        Args:
            user: User object
            bank_account: BankAccount object
            amount: Amount to transfer in EUR
            currency: Currency (default EUR)
        
        Returns:
            Transaction object
        """
        # Get user's wallet
        try:
            wallet = Wallet.objects.get(user=user, currency=currency)
        except Wallet.DoesNotExist:
            raise ValueError(f"User does not have a {currency} wallet")
        
        # Check balance
        if wallet.available_balance < amount:
            raise ValueError("Insufficient balance")
        
        # Calculate fee
        fee_config = TransactionFee.objects.filter(
            transaction_type='SEND_BANK_TRANSFER',
            is_active=True
        ).first()
        
        fee_amount = fee_config.calculate_fee(amount) if fee_config else Decimal('0.00')
        total_amount = amount + fee_amount
        
        # Check balance including fee
        if wallet.available_balance < total_amount:
            raise ValueError("Insufficient balance including fee")
        
        # Create transaction
        txn = Transaction.objects.create(
            user=user,
            transaction_type='SEND_BANK_TRANSFER',
            status='PENDING',
            amount=amount,
            currency=currency,
            fee_amount=fee_amount,
            fee_currency=currency,
            source_wallet=wallet,
            description=f"Transfer to {bank_account.bank_name}",
            metadata={
                'bank_account_id': str(bank_account.id),
                'iban': bank_account.iban[-4:],  # Only last 4 digits for privacy
            }
        )
        
        # Lock the funds in the wallet
        wallet.available_balance -= total_amount
        wallet.locked_balance += total_amount
        wallet.save()
        
        # Create ledger entries
        # Debit user wallet
        LedgerEntry.objects.create(
            transaction=txn,
            entry_type='DEBIT',
            account_type='USER_WALLET',
            amount=amount,
            currency=currency,
            wallet=wallet,
            balance_after=wallet.available_balance,
            description=f"Bank transfer to {bank_account.iban[-4:]}"
        )
        
        # Move to locked account
        LedgerEntry.objects.create(
            transaction=txn,
            entry_type='CREDIT',
            account_type='LOCKED',
            amount=amount,
            currency=currency,
            description=f"Funds locked for bank transfer {txn.id}"
        )
        
        # Fee handling
        if fee_amount > 0:
            LedgerEntry.objects.create(
                transaction=txn,
                entry_type='DEBIT',
                account_type='USER_WALLET',
                amount=fee_amount,
                currency=currency,
                wallet=wallet,
                description=f"Transfer fee for transaction {txn.id}"
            )
            
            LedgerEntry.objects.create(
                transaction=txn,
                entry_type='CREDIT',
                account_type='REVENUE',
                amount=fee_amount,
                currency=currency,
                description=f"Fee revenue from transaction {txn.id}"
            )
        
        return txn
    
    @staticmethod
    @db_transaction.atomic
    def complete_bank_transfer_transaction(transaction_obj):
        """
        Complete a bank transfer transaction.
        
        Args:
            transaction_obj: Transaction object to complete
        """
        if transaction_obj.status not in ['PENDING', 'PROCESSING']:
            raise ValueError(f"Transaction cannot be completed: {transaction_obj.status}")
        
        # Unlock and remove from locked balance
        wallet = transaction_obj.source_wallet
        total_amount = transaction_obj.amount + transaction_obj.fee_amount
        wallet.locked_balance -= total_amount
        wallet.save()
        
        # Update transaction status
        transaction_obj.status = 'COMPLETED'
        transaction_obj.completed_at = timezone.now()
        transaction_obj.save()
        
        # Update ledger - move from locked to final state
        LedgerEntry.objects.create(
            transaction=transaction_obj,
            entry_type='DEBIT',
            account_type='LOCKED',
            amount=transaction_obj.amount,
            currency=transaction_obj.currency,
            description=f"Funds unlocked - transfer completed {transaction_obj.id}"
        )
    
    @staticmethod
    @db_transaction.atomic
    def fail_bank_transfer_transaction(transaction_obj, error_message):
        """
        Fail a bank transfer and refund the user.
        
        Args:
            transaction_obj: Transaction object to fail
            error_message: Error message explaining the failure
        """
        if transaction_obj.status not in ['PENDING', 'PROCESSING']:
            raise ValueError(f"Transaction cannot be failed: {transaction_obj.status}")
        
        # Refund locked funds to available balance
        wallet = transaction_obj.source_wallet
        total_amount = transaction_obj.amount + transaction_obj.fee_amount
        wallet.locked_balance -= total_amount
        wallet.available_balance += total_amount
        wallet.save()
        
        # Update transaction status
        transaction_obj.status = 'FAILED'
        transaction_obj.error_message = error_message
        transaction_obj.save()
        
        # Create refund ledger entries
        LedgerEntry.objects.create(
            transaction=transaction_obj,
            entry_type='DEBIT',
            account_type='LOCKED',
            amount=total_amount,
            currency=transaction_obj.currency,
            description=f"Unlock failed transfer funds {transaction_obj.id}"
        )
        
        LedgerEntry.objects.create(
            transaction=transaction_obj,
            entry_type='CREDIT',
            account_type='USER_WALLET',
            amount=total_amount,
            currency=transaction_obj.currency,
            wallet=wallet,
            balance_after=wallet.available_balance,
            description=f"Refund for failed transfer {transaction_obj.id}"
        )
