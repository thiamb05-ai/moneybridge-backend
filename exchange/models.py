"""
Models for currency exchange rates management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class ExchangeRate(models.Model):
    """Exchange rates between currencies."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Currency pair
    base_currency = models.CharField(_('base currency'), max_length=3)
    quote_currency = models.CharField(_('quote currency'), max_length=3)
    
    # Rate
    rate = models.DecimalField(
        _('exchange rate'),
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text='How much of quote_currency equals 1 unit of base_currency'
    )
    
    # Spread (our markup)
    buy_rate = models.DecimalField(
        _('buy rate'),
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text='Rate at which we buy base_currency'
    )
    sell_rate = models.DecimalField(
        _('sell rate'),
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text='Rate at which we sell base_currency'
    )
    
    # Source
    source = models.CharField(
        _('source'),
        max_length=50,
        default='API',
        help_text='Source of exchange rate (API, Manual, etc.)'
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Timestamps
    effective_from = models.DateTimeField(_('effective from'), auto_now_add=True)
    effective_to = models.DateTimeField(_('effective to'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('exchange rate')
        verbose_name_plural = _('exchange rates')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['base_currency', 'quote_currency', '-created_at']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['base_currency', 'quote_currency', 'effective_from']
    
    def __str__(self):
        return f"{self.base_currency}/{self.quote_currency}: {self.rate}"
    
    @classmethod
    def get_current_rate(cls, base_currency, quote_currency):
        """Get the current active exchange rate."""
        return cls.objects.filter(
            base_currency=base_currency,
            quote_currency=quote_currency,
            is_active=True
        ).order_by('-created_at').first()
    
    def convert(self, amount, direction='sell'):
        """
        Convert amount using this exchange rate.
        
        Args:
            amount: Amount to convert
            direction: 'sell' (base to quote) or 'buy' (quote to base)
        """
        if direction == 'sell':
            # Converting base currency to quote currency
            return amount * self.sell_rate
        else:
            # Converting quote currency to base currency
            return amount / self.buy_rate


class ExchangeRateHistory(models.Model):
    """Historical exchange rates for analytics and reporting."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_currency = models.CharField(_('base currency'), max_length=3)
    quote_currency = models.CharField(_('quote currency'), max_length=3)
    
    # Daily rates
    open_rate = models.DecimalField(_('open rate'), max_digits=15, decimal_places=6)
    high_rate = models.DecimalField(_('high rate'), max_digits=15, decimal_places=6)
    low_rate = models.DecimalField(_('low rate'), max_digits=15, decimal_places=6)
    close_rate = models.DecimalField(_('close rate'), max_digits=15, decimal_places=6)
    
    # Date
    date = models.DateField(_('date'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('exchange rate history')
        verbose_name_plural = _('exchange rate histories')
        ordering = ['-date']
        unique_together = ['base_currency', 'quote_currency', 'date']
        indexes = [
            models.Index(fields=['base_currency', 'quote_currency', '-date']),
        ]
    
    def __str__(self):
        return f"{self.base_currency}/{self.quote_currency} - {self.date}"


class CurrencyConversion(models.Model):
    """Log of all currency conversions performed."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='currency_conversion'
    )
    
    # Conversion details
    from_currency = models.CharField(_('from currency'), max_length=3)
    to_currency = models.CharField(_('to currency'), max_length=3)
    from_amount = models.DecimalField(_('from amount'), max_digits=15, decimal_places=2)
    to_amount = models.DecimalField(_('to amount'), max_digits=15, decimal_places=2)
    
    # Rate used
    exchange_rate = models.ForeignKey(
        ExchangeRate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conversions'
    )
    rate_applied = models.DecimalField(_('rate applied'), max_digits=15, decimal_places=6)
    
    # Timestamp
    converted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('currency conversion')
        verbose_name_plural = _('currency conversions')
        ordering = ['-converted_at']
    
    def __str__(self):
        return f"{self.from_amount} {self.from_currency} → {self.to_amount} {self.to_currency}"
