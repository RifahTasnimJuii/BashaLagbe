from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import UserRegisterForm
import random
from .models import UserProfile
from .forms import OTPForm

from django.utils.translation import gettext as _


def home(request):
    listings = Listing.objects.all()

    # Filters
    area = request.GET.get('area')
    min_rent = request.GET.get('min_rent')
    max_rent = request.GET.get('max_rent')
    rooms = request.GET.get('rooms')
    available_from = request.GET.get('available_from')
    keyword = request.GET.get('q')
    family = request.GET.get('family')  # 'yes' or 'no'

    if area:
        listings = listings.filter(area__name__icontains=area)
    if min_rent:
        listings = listings.filter(price__gte=min_rent)
    if max_rent:
        listings = listings.filter(price__lte=max_rent)
    if rooms:
        listings = listings.filter(rooms=rooms)
    if available_from:
        listings = listings.filter(available_from__lte=available_from)
    if keyword:
        listings = listings.filter(title__icontains=keyword)
    if family == 'yes':
        listings = listings.filter(family_friendly=True)
    elif family == 'no':
        listings = listings.filter(family_friendly=False)

    # Attach cover image
    for listing in listings:
        listing.cover_image = listing.images.filter(is_cover=True).first()

    return render(request, 'core/home.html', {'listings': listings})



def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Generate OTP
            otp = str(random.randint(100000, 999999))
            profile = user.userprofile
            profile.otp = otp
            profile.is_verified = False
            profile.save()

            print(f"📲 OTP for {profile.phone_number}: {otp}")  # For testing

            return redirect('verify_otp')  # redirect to verification page
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('/')


from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from .models import Listing, ListingImage
from .forms import ListingForm, ImageFormSet

@login_required
def create_listing(request):
    if not request.user.userprofile.is_verified:
        messages.warning(request, _("Please verify your phone number to post a listing."))
        return redirect('verify_otp')
    if request.method == 'POST':
        form = ListingForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=ListingImage.objects.none())
        if form.is_valid() and formset.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.latitude = request.POST.get('latitude')   # ✅ Here
            listing.longitude = request.POST.get('longitude') # ✅ Here
            listing.save()
            for image_form in formset.cleaned_data:
                if image_form:
                    image = image_form['image']
                    is_cover = image_form.get('is_cover', False)
                    ListingImage.objects.create(listing=listing, image=image, is_cover=is_cover)
            return redirect('home')
    else:
        form = ListingForm()
        formset = ImageFormSet(queryset=ListingImage.objects.none())
    return render(request, 'core/create_listing.html', {'form': form, 'formset': formset})


@login_required
def verify_otp_view(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            entered = form.cleaned_data['otp']
            if entered == profile.otp:
                profile.is_verified = True
                profile.otp = ''
                profile.save()
                messages.success(request, _("Phone number verified successfully."))
                return redirect('home')
            else:
                messages.error(request, _("Invalid OTP. Try again."))
    else:
        form = OTPForm()
    return render(request, 'core/verify_otp.html', {'form': form})


@login_required
def resend_otp_view(request):
    profile = request.user.userprofile
    otp = str(random.randint(100000, 999999))
    profile.otp = otp
    profile.save()

    print(f"🔁 OTP Resent to {profile.phone_number}: {otp}")
    messages.success(request, _("OTP resent successfully. Please check your phone."))
    return redirect('verify_otp')


from .models import Appointment
from .forms import AppointmentForm

@login_required
def book_appointment(request, listing_id):
    listing = Listing.objects.get(id=listing_id)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.listing = listing
            appointment.user = request.user
            appointment.status = 'pending'
            appointment.save()
            messages.success(request, "Appointment request submitted!")
            return redirect('my_appointments')
    else:
        form = AppointmentForm()
    return render(request, 'core/book_appointment.html', {'form': form, 'listing': listing})

@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/my_appointments.html', {'appointments': appointments})

@login_required
def owner_appointments(request):
    listings = Listing.objects.filter(owner=request.user)
    appointments = Appointment.objects.filter(listing__in=listings).order_by('-created_at')
    return render(request, 'core/owner_appointments.html', {'appointments': appointments})


from .models import RentAgreement
from .forms import RentAgreementForm
from reportlab.pdfgen import canvas
from django.http import HttpResponse
import io


@login_required
def sign_rent_agreement(request, listing_id):
    listing = Listing.objects.get(id=listing_id)

    # Check if already signed
    if RentAgreement.objects.filter(listing=listing).exists():
        return redirect('view_agreement', listing_id=listing.id)

    if request.method == 'POST':
        form = RentAgreementForm(request.POST)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.listing = listing
            agreement.tenant = request.user
            agreement.owner = listing.owner
            agreement.save()
            return redirect('view_agreement', listing_id=listing.id)
    else:
        form = RentAgreementForm()

    return render(request, 'core/sign_agreement.html', {'form': form, 'listing': listing})


@login_required
def view_agreement(request, listing_id):
    agreement = RentAgreement.objects.get(listing_id=listing_id)

    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, f"Rent Agreement for: {agreement.listing.title}")
    p.drawString(100, 780, f"Tenant: {agreement.tenant.username}")
    p.drawString(100, 760, f"Owner: {agreement.owner.username}")
    p.drawString(100, 740, f"Rent Amount: {agreement.rent_amount} BDT")
    p.drawString(100, 720, f"Duration: {agreement.duration_months} months")
    p.drawString(100, 700, f"Tenant Signature: {agreement.tenant_signature}")
    if agreement.owner_signature:
        p.drawString(100, 680, f"Owner Signature: {agreement.owner_signature}")
    p.drawString(100, 660, f"Signed At: {agreement.signed_at.strftime('%Y-%m-%d %H:%M')}")
    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

from .models import RentPayment
from .forms import RentPaymentForm

@login_required
def pay_rent(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    if request.method == 'POST':
        form = RentPaymentForm(request.POST)
        if form.is_valid():
            rent = form.save(commit=False)
            rent.tenant = request.user
            rent.listing = listing
            rent.status = 'paid'
            rent.save()
            messages.success(request, "Rent payment submitted!")
            return redirect('my_rent_history')
    else:
        form = RentPaymentForm()
    return render(request, 'core/pay_rent.html', {'form': form, 'listing': listing})


@login_required
def my_rent_history(request):
    payments = RentPayment.objects.filter(tenant=request.user).order_by('-month')
    return render(request, 'core/my_rent_history.html', {'payments': payments})


@login_required
def manage_rent_payments(request):
    listings = Listing.objects.filter(owner=request.user)
    payments = RentPayment.objects.filter(listing__in=listings).order_by('-month')
    return render(request, 'core/manage_rents.html', {'payments': payments})

