from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-listing/', views.create_listing, name='create_listing'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('appointment/book/<int:listing_id>/', views.book_appointment, name='book_appointment'),
    path('appointment/my/', views.my_appointments, name='my_appointments'),
    path('appointment/manage/', views.owner_appointments, name='owner_appointments'),
    path('agreement/sign/<int:listing_id>/', views.sign_rent_agreement, name='sign_agreement'),
    path('agreement/view/<int:listing_id>/', views.view_agreement, name='view_agreement'),
    path('rent/pay/<int:listing_id>/', views.pay_rent, name='pay_rent'),
    path('rent/my-history/', views.my_rent_history, name='my_rent_history'),
    path('rent/manage/', views.manage_rent_payments, name='manage_rents'),

]
