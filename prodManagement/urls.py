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
    path('productivity/bulletin/summarise', views.SummariseStyleBulletin, name='summariseSytleBulletin'),

    path('productivity/core-sheets', views.CoreSheet, name='coreSheets'),
    path('productivity/core-sheet/add', views.AddCoreSheet, name='addCoreSheet'),
    path('productivity/core-sheet/<int:workOrder>/edit', views.EditCoreSheet, name='editCoreSheet'),
    path('producitivty/core-sheet/orders/missing', options_service.GetOrdersWithMissingCS, name='missingCS'),

    path('productivity/workers', views.Workers, name='workers'),
    path('productivity/worker/add', views.AddWorker, name='addWorker'),
    path('productivity/worker/<int:pk>/edit', views.EditWorker, name='editWorker'),
    path('productivity/api/complete-group', views.MarkGroupCompletion.as_view(), name='groupCompletionAPI'),

    path('options/operations', options_service.GetOperations, name='operationsDropdown'),
    path('options/operations/sections', options_service.GetOperationSections, name='opSecs'),
    path('options/section/<int:pk>', options_service.getOperationSection, name='sectionOperation'),
    path('options/operations/categories', options_service.GetOperationCategories, name='opCats'),
    path('options/machines/types', options_service.GetMachineTypes, name='machTypes'),
    path('options/machines/manufacturers', options_service.GetMachineManufacturers, name='machManufacturers'),

    path('api/temp', views.Temp.as_view(), name='temp'),
]

