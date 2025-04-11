from django.contrib import admin
from . import models

# Register your models here.
@admin.register(models.Operation)
class OperationAdmin(admin.ModelAdmin):
    '''Admin View for Operation'''

    list_display = ('id','Name')
    list_filter = ('Section',)
    search_fields = ('Name',)
