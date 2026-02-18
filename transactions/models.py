"""
Models for transactions and double-entry ledger system.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Transaction(models.Model):
    """Main transaction record."""
    
    TRANSACTION_TYPES = [
        ('RECEIVE_MOBILE_MONEY', 'Receive from Mobile Money'),
        ('SEND_BANK_TRANSFER', 'Send to Bank Account'),
        ('WALLET_TO_WALLET', 'Wallet to Wallet'),
        ('FEE', 'Transaction Fee'),
        ('REFUND', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(_('transaction type'), max_length=50, choices=TRANSACTION_TYPES)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Amount details
    amount = models.DecimalField(
        _('amount'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('currency'), max_length=3)
    
    # Exchange information (if currency conversion)
    original_amount = models.DecimalField(
        _('original amount'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    original_currency = models.CharField(_('original currency'), max_length=3, blank=True)
    exchange_rate = models.DecimalField(
        _('exchange rate'),
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # Fee details
    fee_amount = models.DecimalField(
        _('fee amount'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    fee_currency = models.CharField(_('fee currency'), max_length=3, default='EUR')
    
    # Source and destination
    source_wallet = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='outgoing_transactions'
    )
    destination_wallet = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transactions'
    )
    
    # External references
    external_transaction_id = models.CharField(
        _('external transaction ID'),
        max_length=255,
        blank=True,
        help_text='Transaction ID from payment provider (Wave, Stripe, etc.)'
    )
    
    # Description and metadata
    description = models.TextField(_('description'), blank=True)
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Error handling
    error_code = models.CharField(_('error code'), max_length=50, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('transaction')
        verbose_name_plural = _('transactions')
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['-initiated_at']),
            models.Index(fields=['user', '-initiated_at']),
            models.Index(fields=['status']),
            models.Index(fields=['external_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"


class LedgerEntry(models.Model):
    """Double-entry ledger for all financial transactions."""
    
    ENTRY_TYPES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    ]
    
    ACCOUNT_TYPES = [
        ('USER_WALLET', 'User Wallet'),
        ('REVENUE', 'Revenue'),
        ('FEES', 'Fees'),
        ('PENDING', 'Pending'),
        ('LOCKED', 'Locked'),
        ('FLOAT', 'Float Account'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='ledger_entries')
    
    # Entry details
    entry_type = models.CharField(_('entry type'), max_length=10, choices=ENTRY_TYPES)
    account_type = models.CharField(_('account type'), max_length=20, choices=ACCOUNT_TYPES)
    
    # Amount
    amount = models.DecimalField(
        _('amount'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(_('currency'), max_length=3)
    
    # Reference to wallet if applicable
    wallet = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ledger_entries'
    )
    
    # Balance after this entry
    balance_after = models.DecimalField(
        _('balance after'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Description
    description = models.TextField(_('description'))
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('ledger entry')
        verbose_name_plural = _('ledger entries')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['wallet', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.entry_type} - {self.amount} {self.currency}"


class TransactionLimit(models.Model):
    """Transaction limits based on KYC level."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_level = models.IntegerField(_('KYC level'), unique=True)
    
    # Daily limits
    daily_receive_limit = models.DecimalField(
        _('daily receive limit'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    daily_send_limit = models.DecimalField(
        _('daily send limit'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Per transaction limits
    min_transaction_amount = models.DecimalField(
        _('minimum transaction amount'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_transaction_amount = models.DecimalField(
        _('maximum transaction amount'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Currency (typically EUR as base)
    currency = models.CharField(_('currency'), max_length=3, default='EUR')
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('transaction limit')
        verbose_name_plural = _('transaction limits')
        ordering = ['kyc_level']
    
    def __str__(self):
        return f"KYC Level {self.kyc_level} Limits"


class TransactionFee(models.Model):
    """Fee structure for different transaction types."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_type = models.CharField(_('transaction type'), max_length=50)
    
    # Fee calculation
    fixed_fee = models.DecimalField(
        _('fixed fee'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    percentage_fee = models.DecimalField(
        _('percentage fee'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Percentage (e.g., 1.5 for 1.5%)'
    )
    
    # Min/Max fee
    min_fee = models.DecimalField(
        _('minimum fee'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    max_fee = models.DecimalField(
        _('maximum fee'),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Currency
    currency = models.CharField(_('currency'), max_length=3, default='EUR')
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('transaction fee')
        verbose_name_plural = _('transaction fees')
        ordering = ['transaction_type']
    
    def __str__(self):
        return f"{self.transaction_type} Fee"
    
    def calculate_fee(self, amount):
        """Calculate fee for a given amount."""
        percentage_amount = (amount * self.percentage_fee) / Decimal('100.0')
        total_fee = self.fixed_fee + percentage_amount
        
        # Apply min/max constraints
        if total_fee < self.min_fee:
            total_fee = self.min_fee
        if self.max_fee and total_fee > self.max_fee:
            total_fee = self.max_fee
            
        return total_fee.quantize(Decimal('0.01'))
