from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Area(models.Model):
    name = models.CharField(max_length=100)
    safety_score = models.IntegerField(default=5)  # 1 to 10
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Listing(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    price = models.IntegerField()
    area_size = models.IntegerField(help_text="In square feet")
    rooms = models.IntegerField()
    available_from = models.DateField()

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    has_virtual_tour = models.BooleanField(default=False)
    short_term = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)
    family_friendly = models.BooleanField(default=True)
    female_only = models.BooleanField(default=False)
    single_allowed = models.BooleanField(default=True)

    virtual_tour_video = models.URLField(blank=True, null=True, help_text="YouTube video link of flat tour")

    def __str__(self):
        return f"{self.title} in {self.area}"


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')
    is_360 = models.BooleanField(default=False)
    is_cover = models.BooleanField(default=False)  # This is the main image

    def save(self, *args, **kwargs):
        if self.is_cover:
            # Unset other cover photos for this listing
            ListingImage.objects.filter(listing=self.listing, is_cover=True).update(is_cover=False)
        super().save(*args, **kwargs)


class RentHistory(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    year = models.IntegerField()
    average_rent = models.IntegerField()


class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.user.username

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Only save if profile exists
        try:
            instance.userprofile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.listing.title} at {self.date} {self.time}"


class RentAgreement(models.Model):
    listing = models.OneToOneField(Listing, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, related_name='tenant_agreements', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='owner_agreements', on_delete=models.CASCADE)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    tenant_signature = models.CharField(max_length=255)
    owner_signature = models.CharField(max_length=255, blank=True, null=True)
    signed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Agreement for {self.listing.title}"

class RentPayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('late', 'Late'),
    ]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField(help_text="Set the month for which rent is being paid (e.g., 2025-07-01)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=100, blank=True, null=True)  # e.g. "bKash", "Cash"
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    paid_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.username} - {self.month.strftime('%B %Y')} - {self.status}"


