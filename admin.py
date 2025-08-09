
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Property, PropertyImage, Message, Appointment, Review, VerificationDocument, Amenity, PropertyAmenity

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture', 'about')}),
        ('Permissions', {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('User Type', {'fields': ('user_type',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2'),
        }),
    )

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image', 'is_main', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 1
    raw_id_fields = ('amenity',)

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'landlord', 'property_type', 'price', 'city', 'is_verified', 'is_active')
    list_filter = ('property_type', 'is_verified', 'is_active', 'city')
    search_fields = ('title', 'address', 'city', 'landlord__username')
    raw_id_fields = ('landlord', 'favorited_by')
    inlines = [PropertyImageInline, PropertyAmenityInline]
    fieldsets = (
        (None, {'fields': ('landlord', 'title', 'description')}),
        ('Property Details', {'fields': ('property_type', 'price', 'rental_frequency', 
                                       'bedrooms', 'bathrooms', 'sqft')}),
        ('Location', {'fields': ('address', 'city', 'state', 'zip_code')}),
        ('Status', {'fields': ('is_verified', 'is_active')}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'property', 'is_read', 'sent_at')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('subject', 'body', 'sender__username', 'recipient__username')
    raw_id_fields = ('sender', 'recipient', 'property')

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('property', 'requester', 'landlord', 'requested_date', 'status')
    list_filter = ('status', 'requested_date')
    search_fields = ('property__title', 'requester__username', 'landlord__username')
    raw_id_fields = ('property', 'requester', 'landlord')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewee', 'property', 'rating', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('title', 'content', 'reviewer__username', 'reviewee__username')
    raw_id_fields = ('reviewer', 'reviewee', 'property')

class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'is_approved', 'uploaded_at')
    list_filter = ('is_approved', 'document_type')
    search_fields = ('user__username', 'document_type')
    raw_id_fields = ('user',)

class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

# Add these to your existing admin.py

@admin.action(description='Mark selected properties as verified')
def make_verified(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.action(description='Mark selected properties as unverified')
def make_unverified(modeladmin, request, queryset):
    queryset.update(is_verified=False)

@admin.action(description='Approve selected documents')
def approve_documents(modeladmin, request, queryset):
    queryset.update(is_approved=True)

@admin.action(description='Reject selected documents')
def reject_documents(modeladmin, request, queryset):
    queryset.update(is_approved=False)

# Add actions to the respective ModelAdmin classes
PropertyAdmin.actions = [make_verified, make_unverified]
VerificationDocumentAdmin.actions = [approve_documents, reject_documents]

# Register your models here
admin.site.register(User, CustomUserAdmin)
admin.site.register(Property, PropertyAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(VerificationDocument, VerificationDocumentAdmin)
admin.site.register(Amenity, AmenityAdmin)
admin.site.site_header = "Tenant Network Administration"
admin.site.site_title = "Tenant Network Admin Portal"
admin.site.index_title = "Welcome to Tenant Network Admin"