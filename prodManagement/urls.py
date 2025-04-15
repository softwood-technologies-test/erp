from django.urls import path
from . import views
from .services import options_service

urlpatterns = [
    path('productivity', views.Home, name = 'productivity'),

    path('productivity/operations', views.Operations, name='operations'),

    path('options/operations/sections', options_service.GetOperationSections, name='opSecs'),
    path('options/operations/categories', options_service.GetOperationCategories, name='opCats'),
    path('options/machines/types', options_service.GetMachineTypes, name='machTypes'),
]

