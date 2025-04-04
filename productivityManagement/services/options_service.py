from django.http import JsonResponse, HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required

import pandas as pd

from .. import models

@login_required(login_url='/login')
def GetSections(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=403)
    
    sections = [
        {'value': 'SP', 'text': 'Small Parts'},
        {'value': 'F',  'text': 'Front'},
        {'value': 'B', 'text': 'Back'},
        {'value': 'A1', 'text': 'Assembly 1'},
        {'value': 'A2', 'text': 'Assembly 2'},
        {'value': 'Fin', 'text': 'Finishing'}
    ]
    return JsonResponse(sections, safe=False)

@login_required(login_url='/login')
def getOperations(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=403)
    
    filter = request.GET.get('filter', None)

    if filter == 'Finishing':
        operations = models.OperationsBank.objects.filter(Section=filter) 
    elif filter == 'Stitching':
        filter = ['SP', 'F', 'B', 'A1', 'A2']
        operations = models.OperationsBank.objects.filter(Section__in=filter)
    else:
        operations = models.OperationsBank.objects.all()
    
    fields = ['id','Name']
    operations = operations.values(*fields)
    if operations:
        dfOperations = pd.DataFrame(operations)
    else:
        dfOperations = pd.DataFrame(columns=fields)
    del operations, fields
    
    dfOperations['text'] = dfOperations['id'].astype(str)+' - '+dfOperations['Name'].astype(str)
    dfOperations.drop(inplace=True, columns=['Name'])
    dfOperations.rename(inplace=True, columns={'id': 'value'})

    cols = [i for i in dfOperations]
    data = [dict(zip(cols, i)) for i in dfOperations.values] 
    return JsonResponse(data, safe=False)