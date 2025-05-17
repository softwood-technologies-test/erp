from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import  AllowAny
from rest_framework.request import Request
from rest_framework.authtoken.models import Token
import rest_framework

import json

from .theme import theme
from .services import stitching_service, generic_services, bulletin_service, core_sheet_service
from .services import  worker_service

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
        machine = models.Machine.objects.get(id=pk)
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
        
        context = {
            'data': data,
            'theme': theme,
        }
        return render(request, 'machines/edit.html', context)

@login_required(login_url='/login')
def StyleBulletin(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)

    pageNumber = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    minSAM = request.GET.get('minSAM', None)

    if minSAM:
        minSAM = float(minSAM)

    data = bulletin_service.GetBulletinList(minSAM)
    data = generic_services.applySearch(data, search)
    page = generic_services.paginate(data, pageNumber)

    context = {
        'bulletins': page.object_list, 'page_obj': page,
        'search': search, 'minSAM': minSAM,
        'theme': theme,
    }

    return render(request, 'bulletin/home.html', context)

@login_required(login_url='/login')
def AddStyleBulletin(request: HttpRequest):
    if request.method == 'POST':
        jsonData = json.loads(request.body.decode('utf-8'))

        dfBulletin, dfBulletinDetails = generic_services.refineJson(jsonData)

        try:
            styleBulletinId = bulletin_service.AddStyleBulletin(dfBulletin, dfBulletinDetails)
            return HttpResponse(styleBulletinId, status=200)
        except Exception as e:
            return HttpResponse(e, status=401)
    else:
        context = {
            'theme': theme,
        }

        return render(request, 'bulletin/add.html', context)

@login_required(login_url='/login')
def EditStyleBulletin(request: HttpRequest, pk: int):
    try:
        StyleBulletin = models.StyleBulletin.objects.get(id=pk)
    except:
        return HttpResponse('Resource not found', status=404)

    if request.method == 'POST':
        jsonData = json.loads(request.body.decode('utf-8'))

        dfBulletinDetails = generic_services.refineJson(jsonData)

        try:
            bulletin_service.UpdateStyleBulletin(StyleBulletin, dfBulletinDetails)
            return HttpResponse('Saved Successfully', status=200)
        except Exception as e:
            return HttpResponse(e, status=401)
    else:
        data, operations = bulletin_service.GetDataForBulletin(StyleBulletin)
        context = {
            'data': data,
            'operations': operations, 'operationsJson': json.dumps(list(operations)),
            'theme': theme,
        }
        return render(request, 'bulletin/edit.html', context)

@login_required(login_url='/login')
def DuplicateStyleBulletin(request: HttpRequest, pk: int):
    try:
        styleBulletin = models.StyleBulletin.objects.get(id=pk)
    except:
        return HttpResponse('Resource not found', status=404)
    
    if request.method == 'POST':
        targetCode = request.POST.get('target')

        try:
            styleBulletinId = bulletin_service.DuplicateStyleBulletin(styleBulletin, targetCode)
            return redirect('editStyleBulletin', pk=styleBulletinId)
        except Exception as e:
            print(e)
            return HttpResponse(e, status=401)
    else:
        context = {
            'source': styleBulletin,
            'theme': theme
        }
        return render(request, 'bulletin/duplicate.html', context)

@login_required(login_url='/login')
def SummariseStyleBulletin(request: HttpRequest):
    if request.method != 'POST':
        return HttpResponse('Not Allowed', status=403)

    jsonData = json.loads(request.body.decode('utf-8'))

    operations, id = generic_services.refineJson(jsonData)
    id = int(id.iloc[0, 0])

    try:
        StyleBulletin = models.StyleBulletin.objects.get(id=id)
    except:
        return HttpResponse('Resource Not Found', status=401)

    summary = bulletin_service.SummariseBulletin(StyleBulletin, operations)

    return JsonResponse(summary, safe=False)

class Temp(APIView):
    permission_classes = [AllowAny]
    def post (self, request:Request):
        deviceId = request.data.get('deviceId')  
        tagId = request.data.get('tagId')

        print(f"Tag: {tagId}", f"Device: {deviceId}")

        response = {"message": "Success"}
        status = rest_framework.status.HTTP_200_OK

        return Response (data=response, status=status)

@login_required(login_url='/login')
def CoreSheet (request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    pageNumber = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    workOrder = request.GET.get('workOrder', None)

    try:
        workOrder = models.WorkOrder.objects.get(OrderNumber=workOrder)
    except:
        workOrder = None
    
    data = core_sheet_service.GetCoreSheetList(workOrder)
    data = generic_services.applySearch(data, search)
    page = generic_services.paginate(data, pageNumber)

    context = {
        'coreSheets': page.object_list, 'page_obj': page,
        'search': search,
        'theme': theme,
    }
    if workOrder:
        context.update({'workOrder': workOrder.OrderNumber})
    else:
        context.update({'workOrder': ''})
    return render(request, 'CS/home.html', context)

@login_required(login_url='/login')
def AddCoreSheet (request: HttpRequest):
    if request.method == 'POST':
        pass
    else:
        context = {
            'theme': theme,
        }
        return render(request, 'CS/add.html', context)

@login_required(login_url='/login')
def EditCoreSheet(request: HttpRequest, workOrder: int):
    return HttpResponse('In process')

@login_required(login_url='/login')
def Workers(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    pageNumber = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    department = request.GET.get('department', None)
    status = request.GET.get('status',None)

    if status == 'null':
        status = None
    
    data = worker_service.GetWorkers(department, status)
    data = generic_services.applySearch(data, search)
    page = generic_services.paginate(data, pageNumber)

    context = {
        'workers': page.object_list, 'page_obj': page,
        'search': search, 'department': department, 'status': status,
        'theme': theme,
    }
    return render(request, 'workers/home.html', context)

@login_required(login_url='/login')
def AddWorker(request: HttpRequest):
    if request.method == 'POST':
        fields = ['WorkerCode', 'WorkerName', 'DateOfBirth', 'FatherSpouseName', 'Department', 'SubDepartment', 'CNIC', 'Status', 'Gender', 'User']
        data = {field: request.POST.get(field) for field in fields}

        try:
            workerCode = worker_service.AddWoker(data)
            return redirect(reverse('editWorker', kwargs={'pk': workerCode}))
        except Exception as e:
            print(e)
            context = {
                'error': e, 'data': data,
                'theme': theme,
            }
            return render(request, 'workers/add.html', context)
    else:
        context = {
            'theme': theme,
        }
        return render(request, 'workers/add.html', context)

@login_required(login_url='/login')
def EditWorker(request:HttpRequest, pk: int):
    try:
        worker = models.Worker.objects.get(WorkerCode=pk)
    except:
        return HttpResponse('Resource not found', status=404)

    if request.method == 'POST':
        fields = ['WorkerCode', 'WorkerName', 'DateOfBirth', 'FatherSpouseName', 'Department', 'SubDepartment', 'CNIC', 'Status', 'Gender', 'User', 'DateOfJoining']
        data = {field: request.POST.get(field) for field in fields}

        try:
            worker_service.EditWorker(worker, data)
            url = reverse('workers') + f'?search={worker.WorkerCode}'
            return redirect(url)
        except Exception as e:
            print(e)
            context = {
                'error': e, 'data': data,
                'theme': theme,
            }
            return render(request, 'workers/edit.html', context)
    else:
        data = worker_service.GetDataForWorker(worker)
        context = {
            'data': data,
            'theme': theme
        }
        return render(request, 'workers/edit.html', context)

class MarkGroupCompletion(APIView):
    permission_classes = [AllowAny]

    def post(self, request:Request):
        credentials = request.data.get('credentials')

        try:
            token = Token.objects.get(key=credentials)
        except:
            response = {'error': 'Not authorised'}
            status=  rest_framework.status.HTTP_401_UNAUTHORIZED
            return Response(data=response, status=status)            

        cardId = request.data.get('cardId')

        try:
            core_sheet_service.CompleteCardGroup(cardId)
            
            response = {'message': 'Saved Successfully'}
            status = rest_framework.status.HTTP_200_OK

            return Response (data=response, status=status)
        except Exception as e:
            response = {'error': str(e)}
            status=  rest_framework.status.HTTP_400_BAD_REQUEST
            return Response(data=response, status=status)