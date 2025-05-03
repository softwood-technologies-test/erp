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

@admin.register(models.StyleBulletinOperation)
class StyleBulletinAdmin(admin.ModelAdmin):
    '''Admin View for StyleBulletin'''

    list_display = ('StyleBulletin',)
    list_filter = ('Section',)
    search_fields = ('StyleBulletin','Operation')