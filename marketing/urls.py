from django.urls import path
from . import views
from .services import options_service

urlpatterns = [
    path ('marketing', views.Home, name = 'marketing'),

    path ('marketing/customers', views.CustomerData, name = 'customerData'),
    path ('marketing/customer/add', views.AddCustomer, name='addCustomer'),
    path ('marketing/customer/<int:pk>/edit', views.EditCustomer, name='editCustomer'),


    path('options/countries', options_service.GetCountries, name='countries'),
]