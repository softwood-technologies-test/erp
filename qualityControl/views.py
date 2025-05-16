from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpRequest

import json
from datetime import datetime

from .services import trim_audit_service
from .theme import theme
from .services.generic_services import paginate, applySearch, refineJson

@login_required(login_url='/login')
def Home(request: HttpRequest):
    context = {'theme': theme}
    
    return render (request, 'quality_home.html', context)

@login_required(login_url='/login')
def TrimsAudit (request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not allowed', status=403)
    
    supplier = request.GET.get('supplier', None)
    inventory = request.GET.get('inventory', None)
    startDate = request.GET.get('startDate', None)
    endDate = request.GET.get('endDate', None)
    approval = request.GET.get('approval')
    pageNumber = int(request.GET.get('pageNumber', 1))

    if startDate == 'None':
        startDate = None
    
    if endDate == 'None':
        endDate = None

    if startDate:
        startDate = datetime.strptime(startDate, '%Y-%m-%d').date()
    else:
        startDate = datetime(datetime.now().year, 1, 1).date()
    
    if endDate:
        endDate = datetime.strptime(endDate, '%Y-%m-%d').date()
    else:
        endDate = None
    
    if inventory == 'null':
        inventory = None
    
    if supplier == 'null':
        supplier = None
    
    if approval == 'true':
        approval = True
    elif approval == 'null':
        approval = None
    else:
        approval = False

    data = trim_audit_service.GetAuditHistory(supplier, inventory, approval, startDate, endDate)
    data = paginate(data, pageNumber)

    if not endDate:
        endDate = ''

    context = {
        'audits': data.object_list, 'pageObj': data,
        'supplier': supplier, 'inventory': inventory, 'approval': approval,
        'startDate': startDate, 'endDate': endDate,
        'theme': theme,
    }
    return render(request, 'trim/audit_history.html', context)

@login_required(login_url='/login')
def PendingTrimsAudit (request: HttpRequest):
    if request.method == 'POST':
        jsonData = json.loads(request.body.decode('utf-8'))
        print("Received JSON:", jsonData)  # 🪵 Log raw data

        dfData = refineJson(jsonData)
        print("Refined DataFrame:\n", dfData)  # 🪵 Log refined DataFrame

        try:
            data, checkListOptions = trim_audit_service.PrepareDataForAudit(dfData)
            context = {
                'inv': data, 'checkListOptions': checkListOptions, 
                'theme': theme,
            }
            return render(request,'trim/audit.html', context)
        except Exception as e:
            print("Audit Error:", e)
            return HttpResponse(e, status=400)
    else:
        searchTerm = request.GET.get('searchTerm', '')
        workOrder = request.GET.get('workOrder', None)
        pageNumber = request.GET.get('pageNumber', 1)
        
        if workOrder == 'null':
            workOrder = None

        data = trim_audit_service.GetPendingAudits(workOrder)
        data = applySearch(data, searchTerm)
        data = paginate(data, pageNumber)

        context = {
            'inv': data.object_list, 'pageObj': data,
            'searchTerm': searchTerm, 'workOrder': workOrder,
            'theme': theme
        }
        return render(request, 'trim/home.html', context)

@login_required(login_url='/login')
def AddTrimsAudit(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        # Handle empty payload
        if not request.body:
            raise ValueError("No data received")

        data = json.loads(request.body)
        
        # Validate payload structure
        if not isinstance(data, list):
            raise ValueError("Expected array of audit items")

        trim_audit_service.AddTrimsAudit(data)
        return JsonResponse({'status': 'success', 'message': f'{len(data)} audit items saved'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'type': e.__class__.__name__
        }, status=400)

@login_required(login_url='/login')
def EditTrimsAudit (request: HttpRequest, pk: int):
    if request.method == 'POST':  
        form = request.POST
        
        checks = form.getlist('CheckList')
        approvals = form.getlist('Approval')
        ids = form.getlist('id')
        comments = form.getlist('Comments')
        del form

        formData = {
            'CheckList': checks, 'Approval': approvals,
            'id': ids, 'Comments': comments
        }
        del checks, approvals, ids, comments
        try:
            trim_audit_service.EditTrimsAudit(formData, pk)
            return redirect('trimAudit')
        except Exception as e:
            print(e)
            errorMessage = str(e)
            data, checkListOptions = trim_audit_service.GetAuditsData(pk)
            context = {'audit': data, 'checkListOptions': checkListOptions,
                       'error': errorMessage, 'theme': theme}
            return render(request, 'trim/edit_audit.html', context)   
    else:
        try:
            data, checkListOptions = trim_audit_service.GetAuditsData(pk)
            context = {'audit': data, 'checkListOptions': checkListOptions, 'theme': theme}
            return render(request, 'trim/edit_audit.html', context)
        except Exception as e:
            print(e)
            return HttpResponse(e, status=400)