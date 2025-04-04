from django.contrib import admin
from . import models

from import_export import resources
from import_export.admin import ImportExportModelAdmin

"""class ImpExpResource (resources.ModelResource):
    class Meta:
        model = models.OperationsBank
@admin.register(models.OperationsBank)
class ImpExp(ImportExportModelAdmin):
    list_display = ('id','Name')
    resource_class = ImpExpResource"""

@admin.register(models.OperationsBank)
class OperationsBankAdmin(admin.ModelAdmin):
    '''Admin View for OperationsBank'''

    list_display = ('id','Name', 'SMV')
    list_filter = ('Section',)
    ordering = ('id',)