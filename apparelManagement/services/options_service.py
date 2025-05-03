from django.http import JsonResponse, HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef

import pandas as pd

from .. import models

#Here we serve all the options for dropdowns

@login_required(login_url='/login')
def yesOrNo(request):
    if request.method == 'GET':
        data = {
            "value": [True, False],
            "text": ["Yes", "No"]
        }

        dfData = pd.DataFrame(data)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getCustomersList(request):
    if request.method == 'GET':
        objects = models.Customer.objects.all()     
        dfData = pd.DataFrame(index=range(objects.count()))
        
        dfData['text'] = pd.DataFrame(objects.values('Name'))
        dfData['value'] = pd.DataFrame(objects.values('Name'))

        dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getSuppliersList(request):
    if request.method == 'GET':
        objects = models.Supplier.objects.all()     
        dfData = pd.DataFrame(index=range(objects.count()))
        
        dfData['text'] = pd.DataFrame(objects.values('Name'))
        dfData['value'] = pd.DataFrame(objects.values('Name'))

        dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getDepartmentsList (request: HttpRequest):
    if request.method == 'GET':
        objects = models.Department.objects.all()
        dfData = pd.DataFrame(index=range(objects.count()))

        dfData['text'] = pd.DataFrame(objects.values('FullName'))
        dfData['value'] = pd.DataFrame(objects.values('Name'))

        dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getCategories(request):
    if request.method == 'GET':
        options = models.Categories
        dfData = pd.DataFrame(options)

        dfData.columns = ['value', 'text']

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getInventories(request: HttpRequest):
    if request.method == 'GET':
        invGroup = request.GET.get('group',None)

        if invGroup == 'Direct':
            groups = ['Fabric','Trim']
            objects = models.Inventory.objects.filter(InUse=True).filter(Group__in=groups)
        elif invGroup == 'Indirect':
            groups = ['Electrical','Mechanical','Other','Medicine','Stationery','Housekeeping','Electronics','Fixed Assets']
            objects = models.Inventory.objects.filter(InUse=True).filter(Group__in=groups)
        elif invGroup:
            objects = models.Inventory.objects.filter(InUse=True).filter(Group=invGroup)
        else:
            objects = models.Inventory.objects.filter(InUse=True)
        
        if objects.count() < 1:
            return JsonResponse([], safe=False)

        data = objects.values('Code','Name')
        dfData = pd.DataFrame(data)
        
        dfData['text'] = dfData['Name']+' - '+dfData['Code']
        dfData.drop(inplace=True, columns=['Name'])
        dfData.rename(inplace=True, columns={'Code': 'value'})
        dfData['value'] = dfData['value'].astype(str)
        
        dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]  
        return JsonResponse(data, safe=False)
    else:
        return HttpResponse ('No allowed', status=405)

@login_required(login_url='/login')
def getInvGroups (request: HttpRequest):
    if request.method == 'GET':
        options = models.InvGroups
        dfData = pd.DataFrame(options, columns=['value','text'])

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)
    else:
        return HttpResponse('Not allowed', status=405)

@login_required(login_url='/login')
def getUnits(request):
    if request.method == 'GET':
        objects = models.Unit.objects.all()
        dfData = pd.DataFrame(index=range(objects.count()))

        dfData['text'] = pd.DataFrame(objects.values('Name'))
        dfData['value'] = pd.DataFrame(objects.values('Name'))

        dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]  
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getConsTypes(request):
    if request.method == 'GET':
        options = models.ConsTypes
        dfData = pd.DataFrame(options)

        dfData.columns = ['value', 'text']

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getProductionStages(request):
    if request.method == 'GET':
        options = models.Routes
        dfData = pd.DataFrame(options)

        dfData.columns = ['value', 'text']

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)
    
@login_required(login_url='/login')
def getStyles(request):
    if request.method == 'GET':
        data = models.StyleCard.objects.all().values('StyleCode','Customer')
        dfData = pd.DataFrame(data)
        del data

        dfData['text'] = dfData['Customer']+' - '+dfData['StyleCode']
        dfData.rename(inplace=True, columns={'StyleCode':'value'})
        dfData.drop(inplace=True, columns=['Customer'])

        dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getOrderTypes(request):
    if request.method == 'GET':
        options = models.OrderTypes
        dfData = pd.DataFrame(options)

        dfData.columns = ['value', 'text']

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values]
        return JsonResponse(data, safe=False)
    
@login_required(login_url='/login')
def getCurrencies(request):
    if request.method == 'GET':
        objects = models.Currency.objects.all()
        dfData = pd.DataFrame(index=range(objects.count()))

        dfData['text'] = pd.DataFrame(objects.values('Name'))

        dfData['value'] = pd.DataFrame(objects.values('Code'))
        dfData['value'] = dfData['value'].astype(str)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getMerchandisers(request):
    if request.method == 'GET':
        objects = User.objects.all()
        dfData = pd.DataFrame(index=range(objects.count()))

        dfData = pd.DataFrame(objects.values('first_name','last_name','id'))

        dfData['text'] = dfData['first_name']+' '+dfData['last_name']
        dfData.rename(columns={'id':'value'}, inplace=True)
        dfData.drop(columns=['first_name','last_name'], inplace=True)
        dfData.sort_values(by='text',ascending=True, inplace=True)
        
        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getWorkOrders(request: HttpRequest):
    if request.method == 'GET':
        status = request.GET.get('status', None)
        
        objects = models.WorkOrder.objects.all()
        if objects.count() < 1:
            return JsonResponse([], safe=False)

        data = objects.values('OrderNumber','StyleCode','Customer')
        dfData = pd.DataFrame(data)

        dfData.rename(inplace=True, columns={'OrderNumber':'value'})
        dfData['text'] = dfData['value'].astype(str)+' - '+dfData['StyleCode']+' - '+dfData['Customer']
        dfData.drop(inplace=True, columns=['Customer','StyleCode'])

        dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)
    else:
        return HttpResponse ('No allowed', status=405)

@login_required(login_url='/login')
def getOpenPOs(request:HttpRequest):
    if request.method != 'GET':
        return HttpResponse ('No allowed', status=405)

    #Create a query that checks if a PO number exists in the recept table
    exists = Exists(models.InventoryReciept.objects.filter(PONumber=OuterRef('id')))
    
    #get the po's whose po number doesn't exist in reciept table
    data = models.PurchaseOrder.objects.annotate(received=exists).filter(received=False).values('id', 'Supplier')

    #Generate a dataframe, if there is data, otherwise return empty list
    if data.exists():
        dfData = pd.DataFrame(data)
    else:
        return JsonResponse([{'value': None, 'text': '-----------'}], safe=False)
    
    del data

    #make po number the value of the dropdown
    dfData.rename(inplace=True, columns={'id':'value'})
    
    #Display concatenation of po number and supplier in the dropdown to user
    dfData['text'] = dfData['value'].astype(str)+' - '+dfData['Supplier']
    dfData.drop(inplace=True, columns=['Supplier'])

    #Sort in ascending order w.r.t. po number
    dfData.sort_values(inplace=True, by='value', ascending=True)

    #Append empty row at the start.
    dfData = pd.concat([pd.Series({'value':None, 'text':'-----------'}).to_frame().T, dfData], ignore_index=True)

    cols = [i for i in dfData]
    data = [dict(zip(cols, i)) for i in dfData.values] 
    return JsonResponse(data, safe=False)

@login_required(login_url='/login')
def getUnitsForGroup(request: HttpRequest, group: str):
    if request.method == 'GET':
        objects = models.Unit.objects.filter(Group=group)

        dfData = pd.DataFrame(index=range(objects.count()))

        dfData = pd.DataFrame(objects.values('Name'))

        dfData['text'] = dfData['Name']
        dfData.rename(columns={'Name':'value'}, inplace=True)
        dfData.sort_values(by='text',ascending=True, inplace=True)
        
        cols = [i for i in dfData]
        data = [dict(zip(cols, i)) for i in dfData.values] 
        return JsonResponse(data, safe=False)
    else:
        return HttpResponse('Not allowed', status=405)