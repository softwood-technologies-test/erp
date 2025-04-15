import pandas as pd
import numpy as np

from django.db.models import Q

from .. import models
from . import generic_services

def GetOperations(sectionFilter: str, machineType: str, skillLevel: str, ratePerSAM: str):
    operations = models.Operation.objects

    fields = ['id', 'Name', 'Section', 'Category', 'SkillLevel', 'SMV', 'MachineType', 'Rate']
    filters = Q()
    if sectionFilter:
        filters &= Q(Section=sectionFilter)
    if machineType:
        filters &= Q(MachineType=machineType)
    if skillLevel:
        filters&= Q(SkillLevel=skillLevel)

    if filters:
        operations = operations.filter(filters).values(*fields)
    else:
        operations = operations.all().values(*fields)
    del sectionFilter, machineType, filters

    if operations:
        dfOperations = pd.DataFrame(operations)
    else:
        dfOperations = pd.DataFrame(columns=fields)
    del operations, fields
    
    print(dfOperations)

    return generic_services.dfToListOfDicts(dfOperations)
    