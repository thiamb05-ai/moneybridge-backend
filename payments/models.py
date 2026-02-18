"""
Models for mobile money payment integrations (Wave, Orange Money, MTN MoMo, etc.)
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class MobileMoneyTransaction(models.Model):
    """Mobile money transactions from Africa to MoneyBridge."""
    
    PROVIDERS = [
        ('WAVE', 'Wave'),
        ('ORANGE_MONEY', 'Orange Money'),
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('MOOV_MONEY', 'Moov Money'),
        ('FREE_MONEY', 'Free Money'),
    ]
    
    STATUS_CHOICES = [
        ('INITIATED', 'Initiated'),
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='mobile_money_transaction'
    )
    
    # Provider details
    provider = models.CharField(_('provider'), max_length=50, choices=PROVIDERS)
    provider_transaction_id = models.CharField(
        _('provider transaction ID'),
        max_length=255,
        unique=True,
        blank=True
    )
    
    # Sender details (person sending from Africa)
    sender_phone_number = models.CharField(_('sender phone number'), max_length=20)
    sender_name = models.CharField(_('sender name'), max_length=255, blank=True)
    sender_country = models.CharField(_('sender country'), max_length=3)
    
    # Amount in local currency
    amount = models.DecimalField(
        _('amount'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('currency'), max_length=3)
    
    # Payment method specific data
    payment_method = models.CharField(
        _('payment method'),
        max_length=50,
        default='MOBILE_MONEY'
    )
    
    # Status tracking
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    
    # QR Code payment (for Wave)
    qr_code_reference = models.CharField(_('QR code reference'), max_length=255, blank=True)
    qr_code_expires_at = models.DateTimeField(_('QR code expires at'), null=True, blank=True)
    
    # Webhook data
    webhook_received_at = models.DateTimeField(_('webhook received at'), null=True, blank=True)
    webhook_data = models.JSONField(_('webhook data'), default=dict, blank=True)
    
    # Error handling
    error_code = models.CharField(_('error code'), max_length=50, blank=True)
    error_message = models.TextField(_('error message'), blank=True)
    retry_count = models.IntegerField(_('retry count'), default=0)
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('mobile money transaction')
        verbose_name_plural = _('mobile money transactions')
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['-initiated_at']),
            models.Index(fields=['provider', '-initiated_at']),
            models.Index(fields=['status']),
            models.Index(fields=['provider_transaction_id']),
            models.Index(fields=['qr_code_reference']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.amount} {self.currency}"


class WavePaymentRequest(models.Model):
    """Wave-specific payment request details."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mobile_money_transaction = models.OneToOneField(
        MobileMoneyTransaction,
        on_delete=models.CASCADE,
        related_name='wave_request'
    )
    
    # Wave API specific fields
    wave_transaction_id = models.CharField(_('Wave transaction ID'), max_length=255, unique=True, blank=True)
    wave_checkout_id = models.CharField(_('Wave checkout ID'), max_length=255, blank=True)
    
    # QR Code details
    qr_code_data = models.TextField(_('QR code data'), blank=True)
    qr_code_url = models.URLField(_('QR code URL'), blank=True)
    
    # Payment URL for deep linking
    payment_url = models.URLField(_('payment URL'), blank=True)
    
    # Webhook signature for verification
    webhook_signature = models.CharField(_('webhook signature'), max_length=255, blank=True)
    
    # Status
    is_paid = models.BooleanField(_('is paid'), default=False)
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Wave payment request')
        verbose_name_plural = _('Wave payment requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Wave Request - {self.wave_transaction_id}"


class OrangeMoneyPaymentRequest(models.Model):
    """Orange Money-specific payment request details."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mobile_money_transaction = models.OneToOneField(
        MobileMoneyTransaction,
        on_delete=models.CASCADE,
        related_name='orange_money_request'
    )
    
    # Orange Money API specific fields
    orange_transaction_id = models.CharField(_('Orange transaction ID'), max_length=255, unique=True, blank=True)
    payment_token = models.CharField(_('payment token'), max_length=255, blank=True)
    
    # OTP verification (if required)
    otp_required = models.BooleanField(_('OTP required'), default=False)
    otp_sent_at = models.DateTimeField(_('OTP sent at'), null=True, blank=True)
    
    # Payment notification URL
    notify_url = models.URLField(_('notify URL'), blank=True)
    
    # Status
    is_paid = models.BooleanField(_('is paid'), default=False)
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Orange Money payment request')
        verbose_name_plural = _('Orange Money payment requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Orange Money Request - {self.orange_transaction_id}"


class PaymentWebhook(models.Model):
    """Log of all payment webhooks received."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Provider
    provider = models.CharField(_('provider'), max_length=50)
    
    # Webhook data
    event_type = models.CharField(_('event type'), max_length=100)
    payload = models.JSONField(_('payload'))
    headers = models.JSONField(_('headers'), default=dict)
    
    # Processing status
    is_processed = models.BooleanField(_('is processed'), default=False)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    
    # Error handling
    processing_error = models.TextField(_('processing error'), blank=True)
    retry_count = models.IntegerField(_('retry count'), default=0)
    
    # Related transaction
    mobile_money_transaction = models.ForeignKey(
        MobileMoneyTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks'
    )
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('payment webhook')
        verbose_name_plural = _('payment webhooks')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['-received_at']),
            models.Index(fields=['provider', '-received_at']),
            models.Index(fields=['is_processed']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.received_at}"
