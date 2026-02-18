"""
Models for SEPA instant bank transfers.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class BankTransfer(models.Model):
    """SEPA instant bank transfer from MoneyBridge to user's bank account."""
    
    TRANSFER_TYPES = [
        ('SEPA_INSTANT', 'SEPA Instant'),
        ('SEPA_STANDARD', 'SEPA Standard'),
    ]
    
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='bank_transfer'
    )
    
    # Bank account details
    bank_account = models.ForeignKey(
        'wallets.BankAccount',
        on_delete=models.PROTECT,
        related_name='transfers'
    )
    
    # Transfer details
    transfer_type = models.CharField(_('transfer type'), max_length=20, choices=TRANSFER_TYPES, default='SEPA_INSTANT')
    
    # Amount
    amount = models.DecimalField(
        _('amount'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('currency'), max_length=3, default='EUR')
    
    # Beneficiary information
    beneficiary_name = models.CharField(_('beneficiary name'), max_length=255)
    beneficiary_iban = models.CharField(_('beneficiary IBAN'), max_length=34)
    beneficiary_bic = models.CharField(_('beneficiary BIC'), max_length=11, blank=True)
    
    # Payment reference
    reference = models.CharField(_('reference'), max_length=140, blank=True)
    
    # Status tracking
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    
    # Provider details (Stripe, Modulr, etc.)
    payment_provider = models.CharField(_('payment provider'), max_length=50, default='STRIPE')
    provider_transfer_id = models.CharField(
        _('provider transfer ID'),
        max_length=255,
        unique=True,
        blank=True
    )
    provider_metadata = models.JSONField(_('provider metadata'), default=dict, blank=True)
    
    # Expected arrival time
    expected_arrival_date = models.DateTimeField(_('expected arrival date'), null=True, blank=True)
    actual_arrival_date = models.DateTimeField(_('actual arrival date'), null=True, blank=True)
    
    # Error handling
    error_code = models.CharField(_('error code'), max_length=50, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    failure_reason = models.TextField(_('failure reason'), blank=True)
    retry_count = models.IntegerField(_('retry count'), default=0)
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('bank transfer')
        verbose_name_plural = _('bank transfers')
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['-initiated_at']),
            models.Index(fields=['status']),
            models.Index(fields=['provider_transfer_id']),
            models.Index(fields=['bank_account', '-initiated_at']),
        ]
    
    def __str__(self):
        return f"Transfer to {self.beneficiary_iban[-4:]} - {self.amount} {self.currency}"


class StripeTransferDetails(models.Model):
    """Stripe-specific transfer details."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_transfer = models.OneToOneField(
        BankTransfer,
        on_delete=models.CASCADE,
        related_name='stripe_details'
    )
    
    # Stripe specific IDs
    stripe_payout_id = models.CharField(_('Stripe payout ID'), max_length=255, unique=True, blank=True)
    stripe_balance_transaction_id = models.CharField(
        _('Stripe balance transaction ID'),
        max_length=255,
        blank=True
    )
    stripe_bank_account_id = models.CharField(_('Stripe bank account ID'), max_length=255, blank=True)
    
    # Stripe Connect account (if applicable)
    stripe_connected_account_id = models.CharField(
        _('Stripe connected account ID'),
        max_length=255,
        blank=True
    )
    
    # Fee charged by Stripe
    stripe_fee = models.DecimalField(
        _('Stripe fee'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Status from Stripe
    stripe_status = models.CharField(_('Stripe status'), max_length=50, blank=True)
    
    # Arrival date from Stripe
    stripe_arrival_date = models.DateField(_('Stripe arrival date'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Stripe transfer details')
        verbose_name_plural = _('Stripe transfer details')
    
    def __str__(self):
        return f"Stripe - {self.stripe_payout_id}"


class BankTransferWebhook(models.Model):
    """Log of all bank transfer webhooks received from payment providers."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Provider
    provider = models.CharField(_('provider'), max_length=50)
    
    # Webhook data
    event_type = models.CharField(_('event type'), max_length=100)
    event_id = models.CharField(_('event ID'), max_length=255, unique=True, blank=True)
    payload = models.JSONField(_('payload'))
    headers = models.JSONField(_('headers'), default=dict)
    
    # Signature verification
    signature = models.CharField(_('signature'), max_length=255, blank=True)
    is_verified = models.BooleanField(_('is verified'), default=False)
    
    # Processing status
    is_processed = models.BooleanField(_('is processed'), default=False)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    
    # Error handling
    processing_error = models.TextField(_('processing error'), blank=True)
    retry_count = models.IntegerField(_('retry count'), default=0)
    
    # Related transfer
    bank_transfer = models.ForeignKey(
        BankTransfer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks'
    )
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('bank transfer webhook')
        verbose_name_plural = _('bank transfer webhooks')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['-received_at']),
            models.Index(fields=['provider', '-received_at']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['event_id']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.received_at}"


class BankTransferReturn(models.Model):
    """Returned or rejected bank transfers."""
    
    RETURN_REASONS = [
        ('ACCOUNT_CLOSED', 'Account Closed'),
        ('NO_ACCOUNT', 'No Account'),
        ('INVALID_ACCOUNT_NUMBER', 'Invalid Account Number'),
        ('INSUFFICIENT_FUNDS', 'Insufficient Funds'),
        ('BANK_PROCESSING_ERROR', 'Bank Processing Error'),
        ('BENEFICIARY_DECEASED', 'Beneficiary Deceased'),
        ('OTHER', 'Other Reason'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_transfer = models.OneToOneField(
        BankTransfer,
        on_delete=models.CASCADE,
        related_name='return_details'
    )
    
    # Return information
    return_reason_code = models.CharField(_('return reason code'), max_length=50, choices=RETURN_REASONS)
    return_reason_description = models.TextField(_('return reason description'))
    
    # Return amount (might differ from original due to fees)
    return_amount = models.DecimalField(
        _('return amount'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Bank return reference
    bank_return_reference = models.CharField(_('bank return reference'), max_length=255, blank=True)
    
    # Status
    is_refunded = models.BooleanField(_('is refunded'), default=False)
    refunded_at = models.DateTimeField(_('refunded at'), null=True, blank=True)
    
    # Timestamps
    returned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('bank transfer return')
        verbose_name_plural = _('bank transfer returns')
        ordering = ['-returned_at']
    
    def __str__(self):
        return f"Return - {self.return_reason_code}"
