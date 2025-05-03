from django.urls import path
from . import views
from .services import options_service

urlpatterns = [
    path('productivity', views.Home, name = 'productivity'),

    path('productivity/operations', views.Operations, name='operations'),
    path('productivity/operation/add', views.AddOperation, name='addOperation'),
    path('productivity/operation/<int:pk>/edit', views.EditOperation, name='editOperation'),

    path('productivity/machines', views.Machines, name='machines'),
    path('productivity/machine/add', views.AddMachine, name='addMachine'),
    path('productivity/machine/<int:pk>/edit', views.EditMachine, name='editMachine'),

    path('productivity/bulletins', views.StyleBulletin, name='styleBulletins'),
    path('productivity/bulletin/add', views.AddStyleBulletin, name='addStyleBulletin'),
    path('productivity/bulletin/<int:pk>/edit', views.EditStyleBulletin, name='editStyleBulletin'),
    path('producitivty/bulletin/styles/missing', options_service.GetStylesWithoutBulletins, name='missingStylesForBulletins'),
    path('productivity/bulletin/<int:pk>/duplicate', views.DuplicateStyleBulletin, name='duplicateStyleBulletin'),

    path('options/operations', options_service.GetOperations, name='operationsDropdown'),
    path('options/operations/sections', options_service.GetOperationSections, name='opSecs'),
    path('options/section/<int:pk>', options_service.getOperationSection, name='sectionOperation'),
    path('options/operations/categories', options_service.GetOperationCategories, name='opCats'),
    path('options/machines/types', options_service.GetMachineTypes, name='machTypes'),
    path('options/machines/manufacturers', options_service.GetMachineManufacturers, name='machManufacturers'),
]

