from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages,admin
from django.urls import reverse_lazy
from django.forms import inlineformset_factory
from .models import Property, PropertyImage, Amenity, Message, Appointment, Review, User,PropertyVideo, RentalAgreement, Payment
from .forms import PropertyForm, PropertyImageForm, MessageForm, AppointmentForm, ReviewForm, UserProfileForm, CustomUserCreationForm,PropertyVideoForm, RentalAgreementForm, PaymentForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView,LogoutView
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required,user_passes_test
import stripe
from django.conf import settings


# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def about(request):
    return render(request, 'about.html')

def properties(request):
    return render(request, 'properties.html')

def contact(request):
    return render(request, 'contact.html')

def home(request):
    featured_properties = Property.objects.filter(is_featured=True)[:3]
    return render(request, 'home.html', {
        'featured_properties': featured_properties
    })
@require_POST
def toggle_favorite(request, pk):
    property = get_object_or_404(Property, pk=pk)
    user = request.user
    
    if property in user.favorite_properties.all():
        user.favorite_properties.remove(property)
        is_favorite = False
    else:
        user.favorite_properties.add(property)
        is_favorite = True
    
    return JsonResponse({'is_favorite': is_favorite})

User = get_user_model()

class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'profile_edit.html'
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        messages.success(self.request, 'Profile updated successfully!')
        return reverse_lazy('profile')

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_verified = False
        user.save()
        return super().form_valid(form)

class HomeView(ListView):
    model = Property
    template_name = 'home.html'
    context_object_name = 'featured_properties'
    
    def get_queryset(self):
        return Property.objects.filter(is_active=True, is_verified=True).order_by('-created_at')[:6]

class PropertyListView(ListView):
    model = Property
    template_name = 'listings/property_list.html'
    context_object_name = 'properties'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Property.objects.filter(is_active=True)
        
        property_type = self.request.GET.get('property_type')
        if property_type:
            queryset = queryset.filter(property_type=property_type)
            
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(city__iexact=location)
            
        bedrooms = self.request.GET.get('bedrooms')
        if bedrooms:
            if bedrooms == '3':
                queryset = queryset.filter(bedrooms__gte=3)
            else:
                queryset = queryset.filter(bedrooms=bedrooms)
                
        min_price = self.request.GET.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
            
        max_price = self.request.GET.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset.order_by('-created_at')

class PropertyDetailView(DetailView):
    model = Property
    template_name = 'listings/property_detail.html'
    context_object_name = 'property'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message_form'] = MessageForm(initial={
            'property': self.object,
            'recipient': self.object.landlord
        })
        context['appointment_form'] = AppointmentForm(initial={
            'property': self.object,
            'landlord': self.object.landlord
        })
        if self.request.user.is_authenticated:
            context['is_favorite'] = self.object.favorited_by.filter(id=self.request.user.id).exists()
        return context
    
# views.py
def share_property(request, pk):
    property = get_object_or_404(Property, pk=pk)
    share_url = request.build_absolute_uri(property.get_absolute_url())
    return render(request, 'share.html', {'share_url': share_url})

# urls.py

class PropertyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'listings/property_form.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'landlord'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = PropertyImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['image_formset'] = PropertyImageFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.landlord = self.request.user
            self.object.save()
            
            # Save property images
            images = image_formset.save(commit=False)
            for image in images:
                image.property = self.object
                image.save()
            
            messages.success(self.request, 'Property created successfully!')
            return redirect('property_detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class PropertyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'listings/property_form.html'
    
    def test_func(self):
        property = self.get_object()
        return self.request.user == property.landlord
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = PropertyImageFormSet(
                self.request.POST, self.request.FILES, 
                instance=self.object
            )
        else:
            context['image_formset'] = PropertyImageFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            self.object = form.save()
            
            # Save property images
            images = image_formset.save(commit=False)
            for image in images:
                image.property = self.object
                image.save()
            
            # Delete marked images
            for image in image_formset.deleted_objects:
                image.delete()
            
            messages.success(self.request, 'Property updated successfully!')
            return redirect('property_detail', pk=self.object.pk)
        else:
            return self.render_to_response(self.get_context_data(form=form))

# Define the formset for property images
PropertyImageFormSet = inlineformset_factory(
    Property, 
    PropertyImage, 
    form=PropertyImageForm,
    extra=3,
    max_num=10,
    can_delete=True
)

def property_images(request, pk):
    property = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        form = PropertyImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.property = property
            image.save()
            messages.success(request, 'Image uploaded successfully!')
            return redirect('property_images', pk=property.pk)
    else:
        form = PropertyImageForm()
    
    return render(request, 'listings/property_images.html', {
        'property': property,
        'form': form
    })

class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'messaging/message_form.html'
    
    def form_valid(self, form):
        form.instance.sender = self.request.user
        messages.success(self.request, 'Message sent successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('property_detail', kwargs={'pk': self.object.property.pk})

class AppointmentCreateView(LoginRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/appointment_form.html'
    
    def form_valid(self, form):
        form.instance.requester = self.request.user
        messages.success(self.request, 'Appointment requested successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('property_detail', kwargs={'pk': self.object.property.pk})

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'
    
    def form_valid(self, form):
        form.instance.reviewer = self.request.user
        messages.success(self.request, 'Review submitted successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('property_detail', kwargs={'pk': self.object.property.pk})

class CustomLoginView(LoginView):
    def form_valid(self, form):
        user = form.get_user()
        if not user.is_verified:
            messages.info(self.request, 'Please verify your account to access all features.')
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')  # Replace 'home' with your desired redirect URL
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)
    
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.user_type == 'landlord':
            context['properties'] = Property.objects.filter(landlord=user)
            context['appointments'] = Appointment.objects.filter(
                landlord=user
            ).order_by('-requested_date')[:5]
            context['messages'] = Message.objects.filter(
                recipient=user
            ).order_by('-sent_at')[:5]
            context['reviews'] = Review.objects.filter(
                reviewee=user
            ).order_by('-created_at')[:5]
        else:
            context['favorites'] = user.favorite_properties.all()[:6]
            context['appointments'] = Appointment.objects.filter(
                requester=user
            ).order_by('-requested_date')[:5]
            context['messages'] = Message.objects.filter(
                sender=user
            ).order_by('-sent_at')[:5]
        
        return context

@login_required
def delete_property(request, pk):
    property = get_object_or_404(Property, pk=pk, landlord=request.user)
    
    if request.method == 'POST':
        property.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'property_confirm_delete.html', {'property': property})



# Create your views here.



@user_passes_test(lambda u: u.is_superuser)
def user_stats_view(request):
    landlords = User.objects.filter(user_type='landlord').count()
    tenants = User.objects.filter(user_type='tenant').count()
    verified = User.objects.filter(is_verified=True).count()
    
    context = {
        'landlords': landlords,
        'tenants': tenants,
        'verified': verified,
        'total': landlords + tenants,
    }
    return render(request, 'admin/user_stats.html', context)

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('user-stats/', self.admin_view(user_stats_view), name='user-stats'),
        ]
        return custom_urls + urls


class PropertyVideoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = PropertyVideo
    form_class = PropertyVideoForm
    template_name = 'listings/video_form.html'
    
    def test_func(self):
        property = get_object_or_404(Property, pk=self.kwargs['pk'])
        return self.request.user == property.landlord
    
    def form_valid(self, form):
        form.instance.property = get_object_or_404(Property, pk=self.kwargs['pk'])
        return super().form_valid(form)
    
    def get_success_url(self):
        messages.success(self.request, 'Video uploaded successfully!')
        return reverse('property_detail', kwargs={'pk': self.kwargs['pk']})

class RentalAgreementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = RentalAgreement
    form_class = RentalAgreementForm
    template_name = 'rentals/agreement_form.html'
    
    def test_func(self):
        return self.request.user.user_type == 'landlord'
    
    def form_valid(self, form):
        property = get_object_or_404(Property, pk=self.kwargs['pk'])
        form.instance.property = property
        form.instance.landlord = self.request.user
        form.instance.tenant = get_object_or_404(User, pk=self.kwargs['tenant_pk'])
        return super().form_valid(form)
    
    def get_success_url(self):
        messages.success(self.request, 'Rental agreement created successfully!')
        return reverse('rental_agreement_detail', kwargs={'pk': self.object.pk})

class RentalAgreementDetailView(LoginRequiredMixin, DetailView):
    model = RentalAgreement
    template_name = 'rentals/agreement_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_form'] = PaymentForm(initial={
            'amount': self.object.monthly_rent,
            'payment_date': timezone.now().date(),
            'due_date': self.object.start_date,
        })
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        return context

@login_required
def sign_agreement(request, pk):
    agreement = get_object_or_404(RentalAgreement, pk=pk)
    
    if request.user == agreement.landlord:
        agreement.signed_by_landlord = True
    elif request.user == agreement.tenant:
        agreement.signed_by_tenant = True
    
    if agreement.signed_by_landlord and agreement.signed_by_tenant:
        agreement.status = 'active'
        agreement.signed_at = timezone.now()
        
        # Create first payment record
        Payment.objects.create(
            rental_agreement=agreement,
            amount=agreement.monthly_rent,
            payment_method='stripe',
            status='pending',
            payment_date=timezone.now().date(),
            due_date=agreement.start_date,
        )
    
    agreement.save()
    messages.success(request, 'Agreement signed successfully!')
    return redirect('rental_agreement_detail', pk=agreement.pk)

@login_required
def create_stripe_payment_intent(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        try:
            # Create a PaymentIntent with the order amount and currency
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # amount in cents
                currency='usd',
                metadata={
                    'payment_id': payment.id,
                    'user_id': request.user.id
                }
            )
            
            return JsonResponse({
                'clientSecret': intent.client_secret
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=403)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def payment_success(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment.status = 'completed'
    payment.save()
    
    messages.success(request, 'Payment completed successfully!')
    return redirect('rental_agreement_detail', pk=payment.rental_agreement.pk)

@login_required
def payment_failed(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment.status = 'failed'
    payment.save()
    
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('rental_agreement_detail', pk=payment.rental_agreement.pk)

class AboutView(TemplateView):
    template_name = 'about.html'


def contact_view(request):
    return render(request, 'contact.html')
# views.py

# Replace admin.site = CustomAdminSite() if you want to use the custom admin site