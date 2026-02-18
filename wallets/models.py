"""
Models for user wallets and balances.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Wallet(models.Model):
    """User wallet to hold balance in different currencies."""
    
    CURRENCIES = [
        ('EUR', 'Euro'),
        ('XOF', 'West African CFA Franc'),
        ('XAF', 'Central African CFA Franc'),
        ('GHS', 'Ghanaian Cedi'),
        ('NGN', 'Nigerian Naira'),
        ('KES', 'Kenyan Shilling'),
        ('TZS', 'Tanzanian Shilling'),
        ('UGX', 'Ugandan Shilling'),
        ('ZAR', 'South African Rand'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='wallets')
    currency = models.CharField(_('currency'), max_length=3, choices=CURRENCIES)
    
    # Balance tracking
    available_balance = models.DecimalField(
        _('available balance'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    pending_balance = models.DecimalField(
        _('pending balance'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Balance pending confirmation'
    )
    locked_balance = models.DecimalField(
        _('locked balance'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Balance locked for processing transactions'
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')
        unique_together = ['user', 'currency']
        ordering = ['currency']
    
    def __str__(self):
        return f"{self.user.email} - {self.currency} Wallet"
    
    @property
    def total_balance(self):
        """Total balance including pending and locked."""
        return self.available_balance + self.pending_balance + self.locked_balance


class BankAccount(models.Model):
    """User's linked bank accounts for SEPA transfers."""
    
    ACCOUNT_TYPES = [
        ('CHECKING', 'Checking Account'),
        ('SAVINGS', 'Savings Account'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='bank_accounts')
    
    # Bank details
    bank_name = models.CharField(_('bank name'), max_length=255)
    account_holder_name = models.CharField(_('account holder name'), max_length=255)
    iban = models.CharField(_('IBAN'), max_length=34, unique=True)
    bic_swift = models.CharField(_('BIC/SWIFT'), max_length=11, blank=True)
    account_type = models.CharField(_('account type'), max_length=20, choices=ACCOUNT_TYPES, default='CHECKING')
    
    # Verification
    is_verified = models.BooleanField(_('verified'), default=False)
    verified_at = models.DateTimeField(_('verified at'), null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_default = models.BooleanField(_('default account'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('bank account')
        verbose_name_plural = _('bank accounts')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.account_holder_name} - {self.iban[-4:]}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default account per user
        if self.is_default:
            BankAccount.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class MobileMoneyAccount(models.Model):
    """User's linked mobile money accounts (Wave, Orange Money, etc.)"""
    
    PROVIDERS = [
        ('WAVE', 'Wave'),
        ('ORANGE_MONEY', 'Orange Money'),
        ('MTN_MOMO', 'MTN Mobile Money'),
        ('MOOV_MONEY', 'Moov Money'),
        ('FREE_MONEY', 'Free Money'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='mobile_money_accounts')
    
    # Mobile money details
    provider = models.CharField(_('provider'), max_length=50, choices=PROVIDERS)
    phone_number = models.CharField(_('phone number'), max_length=20)
    account_name = models.CharField(_('account name'), max_length=255)
    country = models.CharField(_('country'), max_length=3)  # ISO 3166-1 alpha-3
    
    # Verification
    is_verified = models.BooleanField(_('verified'), default=False)
    verified_at = models.DateTimeField(_('verified at'), null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('mobile money account')
        verbose_name_plural = _('mobile money accounts')
        unique_together = ['user', 'provider', 'phone_number']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider} - {self.phone_number}"
