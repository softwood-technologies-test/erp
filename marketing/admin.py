from django.contrib import admin
from . import models

from import_export import resources
from import_export.admin import ImportExportModelAdmin

"""class ImpExpResource (resources.ModelResource):
    class Meta:
        model = models.Customer
@admin.register(models.Customer)
class ImpExp(ImportExportModelAdmin):
    list_display = ('id','Name')
    resource_class = ImpExpResource"""

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    '''Admin View for Customer'''
    list_display = ('Name','Country','AccountManager')
    list_filter = ('AccountManager',)
    search_fields = ('Name','Country')

@admin.register(models.CustomerContact)
class CustomerContactAdmin(admin.ModelAdmin):
    '''Admin View for CustomerContact'''

    list_display = ('Customer','Name')
    list_filter = ('Customer',)