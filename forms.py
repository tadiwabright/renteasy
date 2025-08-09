from django import forms
from .models import Property, PropertyImage, Message, Appointment, Review,User,PropertyVideo, RentalAgreement, Payment
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'price', 'rental_frequency',
            'bedrooms', 'bathrooms', 'sqft', 'address', 'city', 'state', 'zip_code'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero")
        return price
    
    def clean_bedrooms(self):
        bedrooms = self.cleaned_data.get('bedrooms')
        if bedrooms < 0:
            raise forms.ValidationError("Bedrooms cannot be negative")
        return bedrooms

class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image', 'is_main']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'property', 'subject', 'body']
        widgets = {
            'recipient': forms.HiddenInput(),
            'property': forms.HiddenInput(),
            'body': forms.Textarea(attrs={'rows': 4}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['property', 'landlord', 'requested_date', 'message']
        widgets = {
            'property': forms.HiddenInput(),
            'landlord': forms.HiddenInput(),
            'requested_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'message': forms.Textarea(attrs={'rows': 4}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['reviewee', 'property', 'rating', 'title', 'content']
        widgets = {
            'reviewee': forms.HiddenInput(),
            'property': forms.HiddenInput(),
            'content': forms.Textarea(attrs={'rows': 4}),
        }

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']  # Add any other fields you want editable


User = get_user_model()

# In forms.py
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(
        choices=User.USER_TYPES,
        widget=forms.RadioSelect,
        required=True
    )
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'user_type', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default help text
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Email/Username', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class PropertyVideoForm(forms.ModelForm):
    class Meta:
        model = PropertyVideo
        fields = ['video', 'title', 'description', 'is_main']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class RentalAgreementForm(forms.ModelForm):
    class Meta:
        model = RentalAgreement
        fields = ['start_date', 'end_date', 'monthly_rent', 'security_deposit', 'terms']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'terms': forms.Textarea(attrs={'rows': 5}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'payment_date', 'due_date']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }