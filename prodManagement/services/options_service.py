"""
Provides the different options for dropdowns etc.
"""

import pandas as pd

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .generic_services import operationSections, operationCategories, machineTypes
from .generic_services import machineManufacturers, dfToListOfDicts
from .. import models

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

@login_required(login_url='/login')
def GetMachineManufacturers(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    return JsonResponse(machineManufacturers, safe=False)

@login_required(login_url='/login')
def GetOperations(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    search = request.GET.get('search', '')
    code = request.GET.get('code', None)
    
    if search:
        operations = models.Operation.objects.filter(Q(Name__icontains=search) | Q(id__icontains=search))[:15]
    else:
        operations = models.Operation.objects.all()
    
    
    if code:
        try:
            operations = operations.filter(id = code)
        except:
            return JsonResponse([], safe=False)

    operations = operations[:15]

    fields = ['id', 'Name']
    operations = operations.values(*fields)

    if operations:
        dfOperations = pd.DataFrame(operations)
    else:
        dfOperations = pd.DataFrame(columns=fields)
    del operations, fields

    dfOperations['Name'] = dfOperations['id'].astype(str)+ ' - '+dfOperations['Name'].astype(str)
    dfOperations.rename(inplace=True, columns={'id': 'value', 'Name':'text'})

    operations = dfToListOfDicts(dfOperations)
    return JsonResponse(operations, safe=False)

@login_required(login_url='/login')
def GetStylesWithoutBulletins (request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=405)

    search = request.GET.get('search', '')
    
    addedStyles = models.StyleBulletin.objects.values_list('StyleCard', flat=True)

    pendingStyles = models.StyleCard.objects.exclude(StyleCode__in=addedStyles)
    if search:
        pendingStyles = pendingStyles.filter(StyleCode__icontains=search)
    
    pendingStyles = pendingStyles[:15]

    fields = ['StyleCode']
    pendingStyles = pendingStyles.values(*fields)
    
    if pendingStyles:
        dfPendingStyles = pd.DataFrame(pendingStyles)
    else:
        dfPendingStyles = pd.DataFrame(columns=fields)
    del pendingStyles, fields
    
    dfPendingStyles['text'] = dfPendingStyles['StyleCode']
    dfPendingStyles.rename(inplace=True, columns={'StyleCode':'value'})
    
    pendingStyles = dfToListOfDicts(dfPendingStyles)
    return JsonResponse(pendingStyles, safe=False)

@login_required(login_url='/login')
def getOperationSection(request, pk):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=405)
    
    section = models.Operation.objects.get(id=pk).Section
    return JsonResponse(section, safe=False)

@login_required(login_url='/login')
def GetOrdersWithMissingCS (request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=405)
    
    search = request.GET.get('search', '')

    addedOrders = models.Cut.objects.values_list('WorkOrder', flat=True)

    pendingOrders = models.WorkOrder.objects.exclude(OrderNumber__in=addedOrders)
    del addedOrders
    if search:
        searchFilter = Q(OrderNumber__icontains=search)
        searchFilter = searchFilter | Q(StyleCode__StyleCode__icontains=search)
        searchFilter = searchFilter | Q(Customer__Name__icontains=search)
        pendingOrders = pendingOrders.filter(searchFilter)
    del search
    
    pendingOrders = pendingOrders[:15]
    
    fields = ['OrderNumber', 'StyleCode', 'Customer']
    pendingOrders = pendingOrders.values(*fields)

    if pendingOrders:
        dfPendingOrders = pd.DataFrame(pendingOrders)
    else:
        dfPendingOrders = pd.DataFrame(columns=fields)
    del pendingOrders, fields

    dfPendingOrders['text'] = dfPendingOrders['OrderNumber'].astype(str) + ' - ' + dfPendingOrders['StyleCode'].astype(str) +' - '+ dfPendingOrders['Customer'].astype(str)
    dfPendingOrders.rename(inplace=True, columns={'OrderNumber': 'value'})
    dfPendingOrders.drop(inplace=True, columns=['StyleCode', 'Customer'])

    pendingOrders = dfToListOfDicts(dfPendingOrders)
    return JsonResponse(pendingOrders, safe=False)