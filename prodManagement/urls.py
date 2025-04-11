from django.urls import path
from . import views

urlpatterns = [
    path('productivity', views.Home, name = 'productivity'),

    path('productivity/operations', views.Operations, name='operations'),
]

