"""
Models for user accounts and KYC management.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """Custom User model with additional fields for MoneyBridge."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=20, unique=True)
    
    # Profile information
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    nationality = models.CharField(_('nationality'), max_length=3, blank=True)  # ISO 3166-1 alpha-3
    country_of_residence = models.CharField(_('country of residence'), max_length=3, blank=True)
    address_line1 = models.CharField(_('address line 1'), max_length=255, blank=True)
    address_line2 = models.CharField(_('address line 2'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    
    # KYC Status
    kyc_status = models.CharField(
        _('KYC status'),
        max_length=30,
        choices=[
            ('NOT_STARTED', 'Not Started'),
            ('PENDING', 'Pending Review'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('ADDITIONAL_INFO_REQUIRED', 'Additional Information Required'),
        ],
        default='NOT_STARTED'
    )
    kyc_level = models.IntegerField(
        _('KYC level'),
        default=0,
        help_text='0: No KYC, 1: Basic KYC, 2: Full KYC'
    )
    kyc_submitted_at = models.DateTimeField(_('KYC submitted at'), null=True, blank=True)
    kyc_approved_at = models.DateTimeField(_('KYC approved at'), null=True, blank=True)
    
    # Account status
    is_active = models.BooleanField(_('active'), default=True)
    is_verified = models.BooleanField(_('email verified'), default=False)
    is_phone_verified = models.BooleanField(_('phone verified'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone_number']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def can_transact(self):
        """Check if user can perform transactions."""
        return self.is_active and self.kyc_status == 'APPROVED'


class KYCDocument(models.Model):
    """KYC documents submitted by users."""
    
    DOCUMENT_TYPES = [
        ('ID_CARD', 'ID Card'),
        ('PASSPORT', 'Passport'),
        ('DRIVERS_LICENSE', 'Driver\'s License'),
        ('RESIDENCE_PERMIT', 'Residence Permit'),
        ('PROOF_OF_ADDRESS', 'Proof of Address'),
        ('SELFIE', 'Selfie'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(_('document type'), max_length=50, choices=DOCUMENT_TYPES)
    document_file = models.FileField(_('document file'), upload_to='kyc_documents/')
    document_number = models.CharField(_('document number'), max_length=100, blank=True)
    
    # Verification status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('PENDING', 'Pending Review'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING'
    )
    rejection_reason = models.TextField(_('rejection reason'), blank=True)
    
    # Metadata
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(_('verified at'), null=True, blank=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('KYC document')
        verbose_name_plural = _('KYC documents')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.document_type}"


class UserActivityLog(models.Model):
    """Log of user activities for audit trail."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(_('activity type'), max_length=50)
    description = models.TextField(_('description'))
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('user activity log')
        verbose_name_plural = _('user activity logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"
