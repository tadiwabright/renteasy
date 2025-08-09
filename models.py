from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
import os
import uuid

def user_profile_pic_path(instance, filename):
    # Upload to: profile_pics/user_<id>/<filename>
    return f'profile_pics/user_{instance.id}/{filename}'

def property_image_path(instance, filename):
    # Upload to: property_images/property_<id>/<filename>
    return f'property_images/property_{instance.property.id}/{filename}'

def verification_doc_path(instance, filename):
    # Upload to: verification_docs/user_<id>/<filename>
    return f'verification_docs/user_{instance.user.id}/{filename}'

class User(AbstractUser):
    LANDLORD = 'landlord'
    TENANT = 'tenant'
    USER_TYPES = [
        (LANDLORD, 'Landlord'),
        (TENANT, 'Tenant'),
    ]
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPES,
        default=TENANT
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to=user_profile_pic_path,
        null=True,
        blank=True,
        help_text="Upload a profile picture (max 2MB)"
    )
    about = models.TextField(blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        swappable = 'AUTH_USER_MODEL'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    # Custom related_name for auth models
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name='tenant_network_user_set',
        related_query_name='tenant_network_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name='tenant_network_user_set',
        related_query_name='tenant_network_user',
    )
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    def get_absolute_url(self):
        return reverse('profile')

class VerificationDocument(models.Model):
    DOCUMENT_TYPES = [
        ('id', 'Government ID'),
        ('proof', 'Proof of Address'),
        ('license', 'Business License'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(
        upload_to=verification_doc_path,
        help_text="Upload a clear photo of your document (max 5MB)"
    )
    is_approved = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Verification Document'
        verbose_name_plural = 'Verification Documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.user.username}'s {self.get_document_type_display()}"

class Property(models.Model):
    PROPERTY_CATEGORIES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('condo', 'Condo'),
        ('townhouse', 'Townhouse'),
        ('studio', 'Studio'),
        ('villa', 'Villa'),
    ]
    
    RENTAL_FREQUENCIES = [
        ('month', 'Monthly'),
        ('week', 'Weekly'),
        ('day', 'Daily'),
    ]
    
    landlord = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='properties',
        limit_choices_to={'user_type': 'landlord'}
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True, editable=False)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_CATEGORIES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    rental_frequency = models.CharField(max_length=10, choices=RENTAL_FREQUENCIES, default='month')
    bedrooms = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    bathrooms = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    sqft = models.PositiveIntegerField(verbose_name="Area (sqft)")
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorited_by = models.ManyToManyField(
        User,
        related_name='favorite_properties',
        blank=True
    )
    
    class Meta:
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.city}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            if not self.id:
                super().save(*args, **kwargs)
            
            base_slug = slugify(f"{self.id}-{self.title}-{self.city}")[:250] if self.title and self.city else f"property-{self.id}"
            self.slug = base_slug
            
            counter = 1
            while Property.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('property_detail', kwargs={'pk': self.pk, 'slug': self.slug})
    
    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()

class PropertyImage(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to=property_image_path,
        help_text="Upload high-quality property images (max 5MB each)"
    )
    is_main = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    caption = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Property Image'
        verbose_name_plural = 'Property Images'
        ordering = ['-is_main', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.property.title}"
    
    def save(self, *args, **kwargs):
        if self.is_main:
            PropertyImage.objects.filter(property=self.property).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

class PropertyVideo(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video = models.FileField(
        upload_to='property_videos/%Y/%m/%d/',
        help_text="Upload a walkthrough video (MP4 format recommended)"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_main = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Property Video'
        verbose_name_plural = 'Property Videos'
        ordering = ['-is_main', 'uploaded_at']
    
    def __str__(self):
        return f"Video for {self.property.title}"

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Font Awesome icon class (e.g., 'fa-wifi')"
    )
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Amenities'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    notes = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Property Amenity'
        verbose_name_plural = 'Property Amenities'
        unique_together = ('property', 'amenity')
    
    def __str__(self):
        return f"{self.property.title} - {self.amenity.name}"

class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages'
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requested_appointments'
    )
    landlord = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hosted_appointments'
    )
    requested_date = models.DateTimeField()
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-requested_date']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
    
    def __str__(self):
        return f"Appointment for {self.property.title} on {self.requested_date}"

class Review(models.Model):
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_reviews'
    )
    reviewee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_reviews'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = ('reviewer', 'property')
    
    def __str__(self):
        return f"{self.rating}★ Review by {self.reviewer}"
    
    def get_absolute_url(self):
        if self.property:
            return reverse('property_detail', kwargs={'pk': self.property.pk})
        return reverse('profile')

class RentalAgreement(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Tenant Approval'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='landlord_agreements')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_agreements')
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    terms = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    signed_by_landlord = models.BooleanField(default=False)
    signed_by_tenant = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rental Agreement for {self.property.title}"
    
    def is_fully_signed(self):
        return self.signed_by_landlord and self.signed_by_tenant
    
    def get_absolute_url(self):
        return reverse('rental_agreement_detail', kwargs={'pk': self.pk})

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    rental_agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    due_date = models.DateField()
    receipt_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment of ${self.amount} for {self.rental_agreement.property.title}"