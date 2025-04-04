from django.urls import path
from . import views
from .services import options_service

urlpatterns = [
    path ('production', views.home, name = 'apparel'),

    path('operations', views.Operations, name='operations'),

    path('ob/stitching', views.StitchingOBs, name='stitchingOBs'),

    path('ob/finsihing', views.FinishingOBs, name='finishingOBs'),

    path('consumption/thread', views.ThreadConsumptions, name='threadConsumption'),

    path('washing/recipe', views.WashingRecipies, name='washingRecipies'),

    path('options/sections', options_service.GetSections, name='productionSections'),
    path('options/operations', options_service.getOperations, name='operationsDropDown'),
]