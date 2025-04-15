from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

from .generic_services import operationSections, operationCategories, machineTypes

@login_required(login_url='/login')
def GetOperationSections(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)

    return JsonResponse(operationSections, safe=False)

@login_required(login_url='/login')
def GetOperationCategories (request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    return JsonResponse(operationCategories, safe=False)

@login_required(login_url='/login')
def GetMachineTypes(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    return JsonResponse(machineTypes, safe=False)