from django.urls import path,include
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomAuthenticationForm
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from .views import (
    HomeView,
    PropertyListView,
    PropertyDetailView,
    PropertyCreateView,
    PropertyUpdateView,
    property_images,
    MessageCreateView,
    AppointmentCreateView,
    ReviewCreateView,
    CustomLoginView,
    DashboardView,
    ProfileView,
    ProfileUpdateView,
    RegisterView,
    delete_property,
    toggle_favorite,    PropertyVideoCreateView, RentalAgreementCreateView, RentalAgreementDetailView,AboutView,
    sign_agreement, create_stripe_payment_intent, payment_success, payment_failed # Make sure this is imported
)

urlpatterns = [
    # Home
    path('', views.HomeView.as_view(), name='home'),
    
    # Properties
    path("admin/", admin.site.urls, name="admin"),
    path('properties/', views.PropertyListView.as_view(), name='property_list'),
    path('properties/<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    path('properties/add/', views.PropertyCreateView.as_view(), name='property_create'),
    path('properties/<int:pk>/edit/', views.PropertyUpdateView.as_view(), name='property_update'),
    path('properties/<int:pk>/images/', views.property_images, name='property_images'),
    path('property/<int:pk>/toggle-favorite/', toggle_favorite, name='toggle_favorite'),
    # Messaging
    path('messages/send/', views.MessageCreateView.as_view(), name='message_create'),
    
    # Appointments
    path('appointments/request/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    
    # Reviews
    path('reviews/create/', views.ReviewCreateView.as_view(), name='review_create'),
    
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('listings/', PropertyListView.as_view(), name='listings'),  
    # User profiles
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html',form_class=CustomAuthenticationForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path("password_reset/",auth_views.PasswordResetView .as_view(), name="password_reset"),
    path('properties/<int:pk>/delete/', delete_property, name='property_delete'),
    path('property/<int:pk>/share/', views.share_property, name='share_property'),
 # Property Videos
    path('property/<int:pk>/video/upload/', PropertyVideoCreateView.as_view(), name='upload_property_video'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', views.contact_view, name='contact'),
    # Rental Agreements
    path('property/<int:pk>/rent/<int:tenant_pk>/', RentalAgreementCreateView.as_view(), name='create_rental_agreement'),
    path('rental-agreement/<int:pk>/', RentalAgreementDetailView.as_view(), name='rental_agreement_detail'),
    path('rental-agreement/<int:pk>/sign/', sign_agreement, name='sign_agreement'),
    
    # Payments
    path('payments/<int:pk>/create-intent/', create_stripe_payment_intent, name='create_payment_intent'),
    path('payments/<int:pk>/success/', payment_success, name='payment_success'),
    path('payments/<int:pk>/failed/', payment_failed, name='payment_failed'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)