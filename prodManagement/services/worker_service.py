import pandas as pd

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from typing import Dict

from .. import models
from . import generic_services

def AddWoker(data: Dict):
    if models.Worker.objects.filter(WorkerCode=data['WorkerCode']).exists():
        raise ValueError('Code Already Exists')
    
    data = {key: None if value == 'null' else value for key, value in data.items()}

    #Convert department and user from string to  object if is provided
    if data['Department']:
        data['Department'] = models.Department.objects.get(Name=data['Department'])
    if data['User']:
        data['User'] = User.objects.get(id=data['User'])

    worker = models.Worker(**data)
    worker.save()

    return worker.WorkerCode