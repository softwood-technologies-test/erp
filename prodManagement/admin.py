from django.contrib import admin
from . import models
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# Register your models here.

"""class ImpExpResource (resources.ModelResource):
    class Meta:
        model = models.Machines
@admin.register(models.Machines)
class ImpExp(ImportExportModelAdmin):
    list_display = ('MachineId', 'Manufacturer', 'Department')
    resource_class = ImpExpResource"""

@admin.register(models.Operation)
class OperationAdmin(admin.ModelAdmin):
    '''Admin View for Operation'''

    list_display = ('id','Name')
    list_filter = ('Section',)
    search_fields = ('Name',)

@admin.register(models.Machines)
class MachinesAdmin(admin.ModelAdmin):
    '''Admin View for Machines'''

    list_display = ('MachineId', 'Manufacturer', 'Department')
    list_filter = ('Department',)
    search_fields = ('MachineId', 'Type',)