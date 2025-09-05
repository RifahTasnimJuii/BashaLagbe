from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserRegisterForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit)
        phone = self.cleaned_data['phone_number']
        profile = UserProfile.objects.get(user=user)
        profile.phone_number = phone
        profile.save()
        return user

class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6)


from .models import Listing, ListingImage
from django.forms import ModelForm, modelformset_factory

class ListingForm(ModelForm):
    class Meta:
        model = Listing
        exclude = ['owner', 'created_at', 'is_verified', 'latitude', 'longitude', 'virtual_tour_video' ]

class ListingImageForm(ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image', 'is_cover']

ImageFormSet = modelformset_factory(ListingImage, form=ListingImageForm, extra=3)

from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

from .models import RentAgreement
from django import forms

class RentAgreementForm(forms.ModelForm):
    class Meta:
        model = RentAgreement
        fields = ['rent_amount', 'duration_months', 'tenant_signature']

from .models import RentPayment
from django import forms

class RentPaymentForm(forms.ModelForm):
    class Meta:
        model = RentPayment
        fields = ['amount', 'month', 'payment_method', 'transaction_id']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'month'}),
        }



