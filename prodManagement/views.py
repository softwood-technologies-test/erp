from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required

from .theme import theme
from .services import stitching_service, generic_services

@login_required(login_url='/login')
def Home (request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)

    context = {'theme': theme}
    return render(request, 'prodManagement/home.html', context)

@login_required(login_url='/login')
def Operations (request:HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    search = request.GET.get('search', '')
    sectionFilter = request.GET.get('sectionFilter', None)
    skillLevel = request.GET.get('skillLevel', None)
    machineType = request.GET.get('machineType', None)
    ratePerSAM = request.GET.get('ratePerSAM', None)

    sectionFilter = None if sectionFilter == 'null' else sectionFilter
    machineType = None if machineType == 'null' else machineType
    skillLevel = None if skillLevel == 'null' else skillLevel
    
    operations = stitching_service.GetOperations(sectionFilter, machineType, skillLevel, ratePerSAM)
    operations = generic_services.applySearch(operations, search)
    page = generic_services.paginate(operations, 1)

    context = {
        'sectionFilter': sectionFilter, 'machineType': machineType, 'ratePerSAM': ratePerSAM,
        'skillLevel': skillLevel, 'search': search,
        'theme': theme,
    }
    return render(request, 'operations/home.html', context)