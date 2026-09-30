from django.urls import path

from . import views
from .webhooks import stripe_webhook

app_name = 'billing'

urlpatterns = [
    path('status/', views.billing_status_view, name='billing_status'),
    path('create-checkout-session/', views.create_checkout_session_view, name='create_checkout'),
    path('customer-portal/', views.customer_portal_view, name='customer_portal'),
    path('webhook/', stripe_webhook, name='stripe_webhook'),
]
