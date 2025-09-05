from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import *

admin.site.register(Area)
admin.site.register(Listing)
admin.site.register(ListingImage)
admin.site.register(RentHistory)
admin.site.register(Review)
admin.site.register(UserProfile)

