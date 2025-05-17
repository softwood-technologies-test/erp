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

""" @admin.register(models.Call)
class CallAdmin(admin.ModelAdmin):
    '''Admin View for Call'''

    list_display = ('Date', 'Caller', 'Customer')
    list_filter = ('Caller',) """