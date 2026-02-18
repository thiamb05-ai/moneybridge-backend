"""
Serializers for transaction API endpoints.
"""
from rest_framework import serializers
from transactions.models import Transaction, LedgerEntry, TransactionFee
from wallets.models import Wallet, BankAccount


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    source_wallet_currency = serializers.CharField(source='source_wallet.currency', read_only=True, allow_null=True)
    destination_wallet_currency = serializers.CharField(source='destination_wallet.currency', read_only=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'user_email', 'transaction_type', 'status',
            'amount', 'currency', 'original_amount', 'original_currency',
            'exchange_rate', 'fee_amount', 'fee_currency',
            'source_wallet', 'source_wallet_currency',
            'destination_wallet', 'destination_wallet_currency',
            'external_transaction_id', 'description', 'metadata',
            'error_code', 'error_message',
            'initiated_at', 'completed_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'exchange_rate', 'fee_amount',
            'external_transaction_id', 'error_code', 'error_message',
            'initiated_at', 'completed_at', 'updated_at'
        ]


class CreateReceiveTransactionSerializer(serializers.Serializer):
    """Serializer for creating a receive transaction from mobile money."""
    
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    currency = serializers.ChoiceField(choices=['XOF', 'XAF', 'GHS', 'NGN', 'KES', 'TZS', 'UGX', 'ZAR'])
    provider = serializers.ChoiceField(choices=['WAVE', 'ORANGE_MONEY', 'MTN_MOMO', 'MOOV_MONEY', 'FREE_MONEY'])
    phone_number = serializers.CharField(max_length=20)
    
    def validate(self, data):
        """Validate the transaction request."""
        user = self.context['request'].user
        
        # Check if user can transact
        if not user.can_transact:
            raise serializers.ValidationError("User is not authorized to transact. Please complete KYC verification.")
        
        return data


class CreateBankTransferSerializer(serializers.Serializer):
    """Serializer for creating a bank transfer."""
    
    bank_account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    reference = serializers.CharField(max_length=140, required=False, allow_blank=True)
    
    def validate_bank_account_id(self, value):
        """Validate that the bank account exists and belongs to the user."""
        user = self.context['request'].user
        try:
            bank_account = BankAccount.objects.get(id=value, user=user, is_active=True)
            if not bank_account.is_verified:
                raise serializers.ValidationError("Bank account is not verified.")
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Bank account not found or does not belong to you.")
        
        return value
    
    def validate(self, data):
        """Validate the bank transfer request."""
        user = self.context['request'].user
        
        # Check if user can transact
        if not user.can_transact:
            raise serializers.ValidationError("User is not authorized to transact. Please complete KYC verification.")
        
        # Check wallet balance
        try:
            wallet = Wallet.objects.get(user=user, currency='EUR')
            if wallet.available_balance < data['amount']:
                raise serializers.ValidationError("Insufficient balance.")
        except Wallet.DoesNotExist:
            raise serializers.ValidationError("EUR wallet not found.")
        
        return data
