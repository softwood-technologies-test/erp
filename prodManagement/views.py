from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .theme import theme
from .services import stitching_service, generic_services
from . import models

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
    pageNumber = request.GET.get('page', 1)

    sectionFilter = None if sectionFilter == 'null' else sectionFilter
    sectionFilter = None if sectionFilter == 'None' else sectionFilter
    machineType = None if machineType == 'null' else machineType
    machineType = None if machineType == 'None' else machineType
    skillLevel = None if skillLevel == 'null' else skillLevel
    skillLevel = None if skillLevel == 'None' else skillLevel
    
    operations = stitching_service.GetOperations(sectionFilter, machineType, skillLevel, ratePerSAM)
    operations = generic_services.applySearch(operations, search)
    page = generic_services.paginate(operations, pageNumber)

    context = {
        'operations': page.object_list, 'page_obj': page,
        'sectionFilter': sectionFilter, 'machineType': machineType, 'ratePerSAM': ratePerSAM,
        'skillLevel': skillLevel, 'search': search,
        'theme': theme,
    }
    return render(request, 'operations/home.html', context)

@login_required(login_url='/login')
def AddOperation (request:HttpRequest):
    if request.method == 'POST':
        fields = ['Name', 'Section', 'Category', 'Level', 'SMV', 'Rate', 'Code', 'Type']
        data = {field: request.POST.get(field) for field in fields}
        
        try:
            opCode = stitching_service.AddOperation(data)
            return redirect(reverse('editOperation', kwargs={'pk': opCode}))
        except Exception as e:
            context = {
                'theme': theme, 'error': e,
            }
            return render(request, 'operations/add.html', context)
    else:
        context = {
            'theme': theme,
        }
        return render(request, 'operations/add.html', context)

@login_required(login_url='/login')
def EditOperation (request: HttpRequest, pk: int):
    try:
        operation = models.Operation.objects.get(id=pk)
    except:
        return HttpResponse('Resource not found', status=404)
    
    if request.method == 'POST':
        fields = ['Name', 'Section', 'Category', 'Level', 'SMV', 'Rate', 'Code', 'Type']
        data = {field: request.POST.get(field) for field in fields}

        try:
            stitching_service.EditOperation(data, operation)
            url = reverse('operations') + f'?search={operation.Name}'
            return redirect(url)
        except Exception as e:
            data = stitching_service.GetDataForOperation(operation)
            context = {
                'data': data, 'error': e,
                'theme': theme,
            }
            return render(request, 'operations/edit.html', context)
        
    else:
        data = stitching_service.GetDataForOperation(operation)
        context = {
            'data': data,
            'theme': theme,
        }
        return render(request, 'operations/edit.html', context)
    
@login_required(login_url='/login')
def Machines(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    search = request.GET.get('search', '')
    type = request.GET.get('type', None)
    status = request.GET.get('status', None)
    manufacturer = request.GET.get('manufacturer', None)
    department = request.GET.get('department', None)
    pageNumber = request.GET.get('page', 1)

    #Convert null in json to None for python handling
    type = None if type == 'null' else type
    status = None if status == 'null' else status
    manufacturer = None if manufacturer == 'null' else manufacturer
    department = None if department == 'null' else department

    machines = stitching_service.GetMachines(type, status, manufacturer, department)
    machines = generic_services.applySearch(machines, search)
    page = generic_services.paginate(machines, pageNumber)
    
    context = {
        'machines': page.object_list, 'page_obj': page,
        'type': type, 'status': status, 'manufacturer': manufacturer, 'search': search,
        'department': department,
        'theme': theme
    }
    return render(request, 'machines/home.html', context)

@login_required(login_url='/login')
def AddMachine(request: HttpRequest):
    if request.method == 'POST':
        fields = ['MachineId', 'Type', 'FunctionStatus', 'Manufacturer', 'ModelNumber', 'SerialNumber', 'Department']
        data = {field: request.POST.get(field) for field in fields}

        try:
            machineCode = stitching_service.AddMachine(data)
            return redirect(reverse('editMachine', kwargs={'pk': machineCode}))
        except Exception as e:
            context = {
                'theme': theme,'error': e,
            }
            return render(request, 'machines/add.html', context)
    else:
        context = {
            'theme': theme,
        }
        return render(request, 'machines/add.html', context)

@login_required(login_url='/login')
def EditMachine(request: HttpResponse, pk: int):
    try:
        machine = models.Machines.objects.get(id=pk)
    except:
        return HttpResponse('Resource not found', status=404)
    
    if request.method == 'POST':
        fields = ['MachineId', 'Type', 'FunctionStatus', 'Manufacturer', 'ModelNumber', 'SerialNumber', 'Department']
        data = {field: request.POST.get(field) for field in fields}
        
        try:
            stitching_service.EditMachine(data, machine)
            url = reverse('machines') + f'?search={machine.MachineId}'
            return redirect(url)
        except Exception as e:
            data = stitching_service.GetDataForMachine(machine)
            context = {
                'data': data, 'error': e,
                'theme': theme,
            }
            return render(request, 'operations/edit.html', context)
    else:
        data = stitching_service.GetDataForMachine(machine)

        print(data)
        
        context = {
            'data': data,
            'theme': theme,
        }
        return render(request, 'machines/edit.html', context)