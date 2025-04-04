import pandas as pd
import numpy as np

from django import forms

from .. import models, theme
from .generic_services import updateModelWithDF, convertTexttoObject, concatenateValues, GST_RATE, LOCAL_CURRENCY

pd.options.mode.chained_assignment = None
pd.set_option('display.max_columns', None)

#Blank form to add data of purchase order
class PurchaseOrderForm(forms.Form):
    DeliveryDate = forms.DateField(
        widget=forms.DateInput(attrs={'class': theme.theme['textInput']}),
        required=True,
    )
    
    Tax = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=True,
        initial=18,
        min_value=0,
    )

#Blank form to create inventories of purchase order
class PurchaseOrderInventoryForm(forms.Form):
    Variant = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=False,
    )

    Quantity = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=True,
        initial=0,
        min_value=0,
    )

    Price = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=True,
        initial=0,
        min_value=0,
    )

    Forex = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=False,
        initial=1,
        min_value=0,
    )

def getInventoryPrice (inventory: models.Inventory):
    '''
    Get the price of inventory. If the inventory is previously ordered, it'll take it's price.
    If not, it'll return the standard price from inventory card.
    If still not found, it'll return Rs. 0.
    '''
    lastPO = models.POInventory.objects.filter(Inventory=inventory).last()
    if lastPO:
        return lastPO.Price, lastPO.Currency.Code
    elif inventory.StandardPrice:
        return inventory.StandardPrice, inventory.Currency.Code
    else:
        return 0.0, LOCAL_CURRENCY

def getLeadTime (Inventories: pd.Series):
    '''
    Get the highes lead-time from a column with inventory objects.
    If none of the inventories have a lead-time, it'll return 0
    '''
    leadTime = 0.0
    for inventory in Inventories:
        try:
            invLeadTime = inventory.LeadTime
        except Exception as e:
            raise ValueError(e)
        if invLeadTime > leadTime:
            leadTime = invLeadTime
    return leadTime

def GeneratePOfromWO(dfData: pd.DataFrame, workOrder: models.WorkOrder):
    '''
    Make a PO for the data from Work Order Table
    '''
    #Calculate the quantity that is required to be ordered.
    dfData[['ReqQuantity','OrderQuantity']] = dfData[['ReqQuantity','OrderQuantity']].astype(float)
    dfData['Quantity'] = dfData['ReqQuantity'] - dfData['OrderQuantity']
    dfData.drop(inplace=True, columns=['ReqQuantity','OrderQuantity'])
    dfData['Quantity'] = dfData['Quantity'].apply(lambda x: round(x, 0))

    dfData = dfData[dfData['Quantity']>0]
    if dfData.empty:
        raise ValueError('All required quantity is ordered.')

    dfData['InventoryCode'] = convertTexttoObject(models.Inventory, dfData['InventoryCode'], 'Code')

    #bifurcate the into three tables, with relevant columns only
    dfInventory = dfData.drop(columns=['Supplier'])
    dfOrder = dfData.drop(columns=['Variant','Quantity'])
    dfAllocation = dfData.drop(columns=['Supplier'])
    del dfData

    dfOrder['Tax'] = GST_RATE

    #Calculate lead-time based on the inventory codes selected
    try:
        dfOrder['LeadTime'] = getLeadTime(dfOrder['InventoryCode'])
    except Exception as e:
        raise ValueError(e)
    dfOrder.drop(inplace=True, columns=['InventoryCode'])

    #Set delivery date, based on the lead time.
    dfOrder['DeliveryDate'] = pd.Timestamp('today') + pd.to_timedelta(dfOrder['LeadTime'], unit='D')
    dfOrder.drop(inplace=True, columns=['LeadTime'])
    dfOrder['DeliveryDate'] = dfOrder['DeliveryDate'].dt.date

    dfOrder['Supplier'] = convertTexttoObject(models.Supplier, dfOrder['Supplier'], 'Name')

    orderCard = {
        'DeliveryDate': dfOrder['DeliveryDate'][0],
        'Supplier': dfOrder['Supplier'][0],
        'Tax': dfOrder['Tax'][0],
    }
    orderCard = models.PurchaseOrder(**orderCard)
    orderCard.save()

    #Set PO Number
    dfInventory['PONumber'] = orderCard

    #Get the prices for the invenotry code, along with the corresponding currency
    dfInventory[['Price','Currency']] = dfInventory['InventoryCode'].apply(getInventoryPrice).apply(pd.Series)

    dfInventory['Currency'] = convertTexttoObject(models.Currency, dfInventory['Currency'], 'Code')

    #TODO: Set this to the current forex rate.
    dfInventory['Forex'] = 1.0

    dfInventory.rename(inplace=True, columns={'InventoryCode':'Inventory'})

    dfInventory.rename(inplace=True, columns={'InventoryCode':'Inventory','OrderQuantity':'Quantity'})
    for _, row in dfInventory.iterrows():
        newEntry = models.POInventory(**row.to_dict())
        newEntry.save()

        flag = (dfAllocation['InventoryCode'] == row['Inventory']) & (dfAllocation['Variant'] == row['Variant'])

        dfAllocation.loc[flag, 'POInvId'] = newEntry 
    
    dfAllocation.drop(inplace=True, columns=['InventoryCode','Variant'])
    dfAllocation['WorkOrder'] = workOrder

    for _, row in dfAllocation.iterrows():
        newEntry = models.POAllocation(**row.to_dict())
        newEntry.save()
    
    return orderCard.id

def GeneratePOfromAutoReq(dfData: pd.DataFrame, supplierName:str):
    '''
    Make a PO for the data from auto-requirement table.
    '''  
    try:
        supplier = models.Supplier.objects.get(Name=supplierName)
    except:
        raise KeyError('Supplier not found') 

    dfData['OrderQuantity'] = dfData['OrderQuantity'].astype(float)
    #Make a duplicate table without any work orders
    dfInventory = dfData.drop(columns=['WorkOrder'])
    dfOrder = dfData.drop(columns=['Variant','OrderQuantity','WorkOrder'])
    dfAllocation = dfData
    del dfData
    
    #Sum the quantity of rows with sam inventory code and variant
    dfInventory = dfInventory.groupby(['InventoryCode','Variant']).sum().reset_index()

    #Convert inventory code to objects of inventory class. This can only be done after the above grouping
    for df in [dfInventory,dfOrder, dfAllocation]:
        df['InventoryCode'] = convertTexttoObject(models.Inventory, df['InventoryCode'], 'Code')

    dfOrder['Tax'] = GST_RATE
    try:
        dfOrder['LeadTime'] = getLeadTime(dfOrder['InventoryCode'])
    except Exception as e:
        raise ValueError(e)
    dfOrder.drop(inplace=True, columns=['InventoryCode'])
    
    #Set delivery date, based on the lead time.
    dfOrder['DeliveryDate'] = pd.Timestamp('today') + pd.to_timedelta(dfOrder['LeadTime'], unit='D')
    dfOrder.drop(inplace=True, columns=['LeadTime'])
    dfOrder['DeliveryDate'] = dfOrder['DeliveryDate'].dt.date

    orderCard = {
        'DeliveryDate': dfOrder['DeliveryDate'][0],
        'Supplier': supplier,
        'Tax': dfOrder['Tax'][0],
    }
    orderCard = models.PurchaseOrder(**orderCard)
    orderCard.save()

    #Set PO Number
    dfInventory['PONumber'] = orderCard

    #Get the prices for the invenotry code, along with the corresponding currency
    dfInventory[['Price','Currency']] = dfInventory['InventoryCode'].apply(getInventoryPrice).apply(pd.Series)

    dfInventory['Currency'] = convertTexttoObject(models.Currency, dfInventory['Currency'], 'Code')

    #TODO: Set this to the current forex rate.
    dfInventory['Forex'] = 1.0

    dfInventory.rename(inplace=True, columns={'InventoryCode':'Inventory','OrderQuantity':'Quantity'})
    dfInventory['Quantity'] = dfInventory['Quantity'].apply(lambda x: round(x, 0))
    for _, row in dfInventory.iterrows():
        newEntry = models.POInventory(**row.to_dict())
        newEntry.save()

        flag = (dfAllocation['InventoryCode'] == row['Inventory']) & (dfAllocation['Variant'] == row['Variant'])

        dfAllocation.loc[flag, 'POInvId'] = newEntry   

    dfAllocation.drop(inplace=True, columns=['InventoryCode','Variant'])

    dfAllocation.rename(inplace=True, columns={'OrderQuantity':'Quantity'})

    dfAllocation['WorkOrder'] = dfAllocation['WorkOrder'].astype(int)
    dfAllocation['WorkOrder'] = convertTexttoObject(models.WorkOrder, dfAllocation['WorkOrder'], 'OrderNumber')
    
    for _, row in dfAllocation.iterrows():
        newEntry = models.POAllocation(**row.to_dict())
        newEntry.save()

    return orderCard.id

def PrepareDataForAutoReq(startingOrder: int, endingOrder: int):
    '''
    Get all unordered accessories for auto requirement
    '''
    if not startingOrder:
        return None, None

    requirement = models.InvRequirement.objects.filter(OrderNumber__gte=startingOrder).filter(OrderNumber__lte=endingOrder)
    requirement = requirement.values('OrderNumber','InventoryCode','Variant','Quantity')
    if requirement:
        dfRequirement = pd.DataFrame(requirement)
    else:
        dfRequirement = pd.DataFrame(columns=['OrderNumber','InventoryCode','Variant','Quantity'])
    del requirement

    if dfRequirement.empty:
        return None, None

    poAllocation = models.POAllocation.objects.filter(WorkOrder__gte=startingOrder).filter(WorkOrder__lte=endingOrder)
    poAllocation = poAllocation.values('POInvId','WorkOrder','Quantity')
    if poAllocation:
        dfAllocation = pd.DataFrame(poAllocation)
    else:
        dfAllocation = pd.DataFrame(columns=['POInvId','WorkOrder','Quantity'])
    del poAllocation

    poInventory = models.POInventory.objects.filter(id__in=dfAllocation['POInvId'].to_list())
    poInventory = poInventory.values('id','Inventory','Variant')
    if poInventory:
        dfPOInventory = pd.DataFrame(poInventory)
    else:
        dfPOInventory = pd.DataFrame(columns=['id','Inventory','Variant'])
    del poInventory

    inventories = models.Inventory.objects.filter(Code__in=dfRequirement['InventoryCode'].to_list()).values('Code','Name')
    if inventories:
        dfInventories = pd.DataFrame(inventories)
    else:
        dfInventories = pd.DataFrame(columns=['Code','Name'])
    del inventories

    dfRequirement.rename(inplace=True, columns={'Quantity':'Required'})

    dfRequirement = pd.merge(left=dfRequirement, right=dfInventories, left_on='InventoryCode', right_on='Code', how='left')
    dfRequirement.rename(inplace=True, columns={'Name':'InventoryName'})
    dfRequirement.drop(inplace=True, columns=['Code'])

    if not dfAllocation.empty:
        dfAllocation = pd.merge(left=dfAllocation, right=dfPOInventory, left_on='POInvId', right_on='id', how='left')
        dfAllocation.drop(inplace=True, columns=['POInvId','id'])
        dfAllocation.rename(inplace=True, columns={'Quantity':'Ordered'})

        dfRequirement = pd.merge(left=dfRequirement, right=dfAllocation, left_on=['OrderNumber','InventoryCode','Variant']
                                 ,right_on=['WorkOrder','Inventory','Variant'], how='left')
        dfRequirement.drop(inplace=True, columns=['Inventory'])
        
        dfRequirement['Ordered'] = np.where(dfRequirement['Ordered'].isna(), 0, dfRequirement['Ordered'])
    else:
        dfRequirement['Ordered'] = 0
    
    dfRequirement['ToOrder'] = dfRequirement['Required'] - dfRequirement['Ordered']
    dfRequirement = dfRequirement[dfRequirement['ToOrder']>0]

    dfRequirement.sort_values(by='InventoryCode', ascending=True, inplace=True)

    dfInventories = dfRequirement[['InventoryCode','InventoryName']]
    dfInventories = dfInventories.drop_duplicates(subset=['InventoryCode'], keep='first')
    dfInventories.rename(inplace=True, columns={'InventoryCode':'value','InventoryName':'text'})
    
    cols = [i for i in dfInventories]
    invs = [dict(zip(cols, i)) for i in dfInventories.values]

    cols = [i for i in dfRequirement]
    requirement = [dict(zip(cols, i)) for i in dfRequirement.values]

    return requirement, invs

def GetOrderList(searchTerm: str, supplier: str, poNumber: int):
    '''
    Get the list of all purchase orders
    '''
    if poNumber:
        orders = models.PurchaseOrder.objects.filter(id=poNumber)
    elif supplier:
        orders = models.PurchaseOrder.objects.filter(Supplier=supplier)
    else:
        orders = models.PurchaseOrder.objects.all()
    
    orders = orders.values('id','OrderDate','DeliveryDate','Supplier')
    dfOrders = pd.DataFrame(orders)
    del orders

    if dfOrders.empty:
        return []

    inventories = models.POInventory.objects.filter(PONumber__in=dfOrders['id'].to_list())
    inventories = inventories.values('id','PONumber','Inventory')
    dfInventories = pd.DataFrame(inventories)
    del inventories

    allocations = models.POAllocation.objects.filter(POInvId__in=dfInventories['id'].to_list())
    allocations = allocations.values('POInvId','WorkOrder')
    dfAllocations = pd.DataFrame(allocations)
    del allocations

    inventoryCards = models.Inventory.objects.filter(Code__in=dfInventories['Inventory'].to_list())
    inventoryCards = inventoryCards.values('Code','Name')
    dfInventoryCards = pd.DataFrame(inventoryCards)
    del inventoryCards
    
    #Give verbose names to the id columns
    dfOrders.rename(inplace=True, columns={'id':'PONumber'})
    dfInventories.rename(inplace=True, columns={'id':'POInvId'})

    dfOrders = pd.merge(left=dfOrders, right=dfInventories, left_on='PONumber', right_on='PONumber', how='left')
    del dfInventories

    dfOrders = pd.merge(left=dfOrders, right=dfAllocations, left_on='POInvId', right_on='POInvId', how='left')
    dfOrders.drop(inplace=True, columns=['POInvId'])
    del dfAllocations

    dfOrders = pd.merge(left=dfOrders, right=dfInventoryCards, left_on='Inventory', right_on='Code', how='left')
    dfOrders.drop(inplace=True, columns=['Inventory','Code'])
    del dfInventoryCards

    #Convert work order float to string, without decimals
    dfOrders['WorkOrder'] = np.where(dfOrders['WorkOrder'].isna(), 0, dfOrders['WorkOrder'])
    dfOrders['WorkOrder'] = dfOrders['WorkOrder'].astype(int).astype(str)
    dfOrders['WorkOrder'] = np.where(dfOrders['WorkOrder']=='0', '', dfOrders['WorkOrder'])

    #Concate rows who have same PO number in common
    dfOrders = dfOrders.groupby('PONumber').agg({
        'DeliveryDate': 'first',
        'Supplier': 'first',
        'Name': concatenateValues,
        'WorkOrder': concatenateValues,
    }).reset_index()

    searchTerm = searchTerm.lower()
    mask = dfOrders.apply(lambda row: any(searchTerm in str(val).lower() for val in row.values), axis=1)
    dfOrders = dfOrders[mask]

    dfOrders = dfOrders.sort_values(by='PONumber', ascending=False)
    
    cols = [i for i in dfOrders]
    data = [dict(zip(cols, i)) for i in dfOrders.values]
    return data

def AddPurchaseOrder(OrderDF: pd.DataFrame, InventoryDF: pd.DataFrame, AllocationDF:pd.DataFrame):
    '''
    Add the PO from new PO Form
    '''
    OrderDF['Supplier'] = convertTexttoObject(models.Supplier, OrderDF['Supplier'], 'Name')

    OrderDF['DeliveryDate'] = pd.to_datetime(OrderDF["DeliveryDate"], format="%m/%d/%Y")

    OrderDF['Tax'] = OrderDF['Tax'].astype(float)

    orderCard = {
        'DeliveryDate': OrderDF['DeliveryDate'][0],
        'Supplier': OrderDF['Supplier'][0],
        'Tax': OrderDF['Tax'][0],
    }
    orderCard = models.PurchaseOrder(**orderCard)
    orderCard.save() 

    #Convert fields to required format and handle empty cells
    InventoryDF['Currency']=np.where(InventoryDF['Currency'].str.len()==0, 'PKR', InventoryDF['Currency'])
    InventoryDF['Quantity'] = np.where(InventoryDF['Quantity'].str.len()==0, 0, InventoryDF['Quantity'])
    InventoryDF['Price'] = np.where(InventoryDF['Price'].str.len()==0, 0, InventoryDF['Price'])
    InventoryDF['Forex'] = np.where(InventoryDF['Forex'].str.len()==0, 1, InventoryDF['Forex'])
    InventoryDF['Quantity'] = InventoryDF['Quantity'].astype(float)
    InventoryDF['Price'] = InventoryDF['Price'].astype(float)
    InventoryDF['Forex'] = InventoryDF['Forex'].astype(float) 

    if InventoryDF.empty:
        raise ValueError('No Inventory provided')
    
    #Set PO Number
    InventoryDF['PONumber'] = orderCard

    #Remove rows without inventory code
    InventoryDF = InventoryDF[InventoryDF['InvCode'].str.len()>0]
    
    InventoryDF['InvCode'] = convertTexttoObject(models.Inventory, InventoryDF['InvCode'], 'Code')

    InventoryDF['Currency'] = convertTexttoObject(models.Currency, InventoryDF['Currency'], 'Code')

    InventoryDF['Quantity'] = InventoryDF['Quantity'].apply(lambda x: round(x, 0))

    InventoryDF.rename(inplace=True, columns={'InvCode':'Inventory'})

    #The inventory code on which the allocation is made
    allocationInvVariant = str(OrderDF['allocationInvCode'][0])
    allocationInvVariant = allocationInvVariant.split('_')

    #Save the inventories and set the object for which to save allocations
    poInvObj = None
    for index, row in InventoryDF.iterrows():
        try:  
            newEntry = models.POInventory(**row.to_dict())
            newEntry.save()

            if not allocationInvVariant:
                if (row['Inventory'].Code == allocationInvVariant[0]) & (row['Variant'] == allocationInvVariant[1]):
                    poInvObj = newEntry
  
        except Exception as e:
            raise ValueError(f"Cannot save at {index}: {e}")
    
    #Save the allocaiton if is provided
    if poInvObj and not AllocationDF.empty:
        AllocationDF = AllocationDF.replace('null', '')
        
        AllocationDF['POInvId'] = poInvObj 

        AllocationDF['WorkOrder'] = convertTexttoObject(models.WorkOrder, AllocationDF['WorkOrder'], 'OrderNumber')

        for index, row in AllocationDF.iterrows():
            try:
                pass
                newEntry = models.POAllocation(**row.to_dict())
                newEntry.save()
            except Exception as e:
                raise ValueError(f"Cannot save at {index}: {e}")
    
    #Return PO Number to redirect user to
    return orderCard.id

def EditPurchaseOrder(
        orderObject: models.PurchaseOrder,
        OrderDF: pd.DataFrame,
        InventoryDF: pd.DataFrame,
        AllocationDF:pd.DataFrame
        ):
    '''
    Update the PO from the data in the PO table.
    '''
    OrderDF['Supplier'] = convertTexttoObject(models.Supplier, OrderDF['Supplier'], 'Name')

    OrderDF['DeliveryDate'] = pd.to_datetime(OrderDF["DeliveryDate"], format="%m/%d/%Y")

    OrderDF['Tax'] = OrderDF['Tax'].astype(float)

    #Update order object to as provided by user and save it.
    orderObject.Supplier = OrderDF['Supplier'][0]
    orderObject.DeliveryDate = OrderDF['DeliveryDate'][0]
    orderObject.Tax = OrderDF['Tax'][0]
    orderObject.save()

    #Get the already saved inventories against this PO and their allocation
    previousInventories = models.POInventory.objects.filter(PONumber=orderObject).values('id','Inventory','Variant')
    if previousInventories:
        dfPreviousInventories = pd.DataFrame(previousInventories)
    else:
        dfPreviousInventories = pd.DataFrame(columns=['id','Inventory','Variant'])
    del previousInventories

    #Convert fields to required format and handle empty cells
    InventoryDF['Currency']=np.where(InventoryDF['Currency'].str.len()==0, 'PKR', InventoryDF['Currency'])
    InventoryDF['Quantity'] = np.where(InventoryDF['Quantity'].str.len()==0, 0, InventoryDF['Quantity'])
    InventoryDF['Price'] = np.where(InventoryDF['Price'].str.len()==0, 0, InventoryDF['Price'])
    InventoryDF['Forex'] = np.where(InventoryDF['Forex'].str.len()==0, 1, InventoryDF['Forex'])
    InventoryDF['Quantity'] = InventoryDF['Quantity'].astype(float)
    InventoryDF['Price'] = InventoryDF['Price'].astype(float)
    InventoryDF['Forex'] = InventoryDF['Forex'].astype(float) 

    if InventoryDF.empty:
        raise ValueError('No Inventory provided')

    InventoryDF = pd.merge(left=InventoryDF, right=dfPreviousInventories, left_on=['InvCode','Variant'],
                           right_on=['Inventory','Variant'], how='left')
    InventoryDF.drop(inplace=True, columns=['Inventory'])
    
    InventoryDF['InvCode'] = convertTexttoObject(models.Inventory, InventoryDF['InvCode'], 'Code')

    InventoryDF['Currency'] = convertTexttoObject(models.Currency, InventoryDF['Currency'], 'Code')
    
    InventoryDF.rename(inplace=True, columns={'InvCode':'Inventory'})
    
    InventoryDF['PONumber'] = orderObject

    try:
        updateModelWithDF(targetTable=models.POInventory, newData=InventoryDF, previousData=dfPreviousInventories)
    except Exception as e:
        raise ValueError (e)

    #The inventory code on which the allocation is made
    allocationInvVariant = str(OrderDF['allocationInvCode'][0])
    allocationInvVariant = allocationInvVariant.split('_')

    AllocationDF = AllocationDF[~AllocationDF['WorkOrder'].isna()]
    #Save the allocaiton if it is provided
    if not AllocationDF.empty:
        AllocationDF['WorkOrder'] = AllocationDF['WorkOrder'].astype(int)

        try:
            POInvObj = models.POInventory.objects.get(PONumber=orderObject, Inventory=allocationInvVariant[0], Variant=allocationInvVariant[1])
            AllocationDF['POInvId'] = POInvObj
        except Exception as e:
            raise ValueError(e)
        
        previousAllocations = models.POAllocation.objects.filter(POInvId=POInvObj).values('id','WorkOrder')
        dfPreviousAllocations = pd.DataFrame(previousAllocations)
        del previousAllocations
        
        if dfPreviousAllocations.empty:
            AllocationDF['id'] = None
        else:
            AllocationDF = pd.merge(left=AllocationDF, right=dfPreviousAllocations, left_on='WorkOrder', right_on='WorkOrder', how='left')

        AllocationDF['WorkOrder'] = convertTexttoObject(models.WorkOrder, AllocationDF['WorkOrder'], 'OrderNumber')

        try:
            updateModelWithDF(targetTable=models.POAllocation, newData=AllocationDF, previousData=dfPreviousAllocations)
        except Exception as e:
            raise ValueError (e)
        
def getPOAllocation(inventoryCode: str, variant: str, urlPath: str):
    '''
    Get the allocation of an inventory code in a provided PO.
    '''
    urlParts = urlPath.strip('/').split('/')
    del urlPath

    if len(urlParts) == 2:
        #This is true for a new PO and there would be no allocation
        return
    elif len(urlParts) == 3:
        poNumber = int(urlParts[1])
        poObject = models.PurchaseOrder.objects.get(id=poNumber)

        poInventory = models.POInventory.objects.get(PONumber=poObject, Inventory=inventoryCode, Variant=variant)

        allocation = models.POAllocation.objects.filter(POInvId=poInventory)
        allocation = allocation.values('WorkOrder','Quantity')

        if allocation:
            return list(allocation)
        else:
            return None
    else:
        raise SyntaxError('Invalid Input')

def getAllocatedQty (purchaseOrder: models.PurchaseOrder, inventory: models.Inventory, variant: str):
    poInventory = models.POInventory.objects.get(PONumber=purchaseOrder, Inventory=inventory, Variant=variant)

    allocations = models.POAllocation.objects.filter(POInvId=poInventory).values('Quantity')

    allocatedQty = 0.0
    for item in allocations:
        allocatedQty = allocatedQty + item['Quantity']

    return allocatedQty

def ProcessOrderData(orderObject: models.PurchaseOrder):
    '''
    Get the data of the provided PO.
    '''
    order = {
        'PONumber': orderObject.id,
        'OrderDate': orderObject.OrderDate,
        'DeliveryDate': orderObject.DeliveryDate,
        'Supplier': orderObject.Supplier.Name,
        'Tax': orderObject.Tax
    }

    inventories = models.POInventory.objects.filter(PONumber=orderObject)
    inventories = inventories.values('id','Inventory','Variant','Quantity','Price','Currency','Forex')
    
    return order, inventories

def GetWorkOrderDefaultQty (
        workOrder: models.WorkOrder,
        inventory: models.Inventory,
        variant: str,
        currentPO: models.PurchaseOrder
        ):
    '''
    Get the default qty to show user for allocation box.
    '''
    requirement = models.InvRequirement.objects.filter(OrderNumber=workOrder, InventoryCode=inventory, Variant=variant)
    
    if not requirement:
        return 0.0
    
    requirement = requirement.values('InventoryCode','Variant','Quantity')
    dfRequirement = pd.DataFrame(requirement)
    del requirement
    
    previouslyOrdered = models.POAllocation.objects.filter(WorkOrder=workOrder).values('POInvId','Quantity')
    dfPreviouslyOrdered = pd.DataFrame(previouslyOrdered)
    del previouslyOrdered

    orderedInv = models.POInventory.objects.filter(id__in = dfPreviouslyOrdered['POInvId'].to_list()).exclude(PONumber=currentPO)
    orderedInv = orderedInv.values('id','Inventory','Variant')
    dfOrderedInv = pd.DataFrame(orderedInv)
    del orderedInv

    dfPreviouslyOrdered = pd.merge(left=dfPreviouslyOrdered, right=dfOrderedInv, left_on='POInvId', right_on='id', how='left')
    del dfOrderedInv
    dfPreviouslyOrdered.drop(inplace=True, columns=['POInvId','id'])

    dfRequirement.rename(inplace=True, columns={'InventoryCode':'Inventory', 'Quantity':'RequiredQty'})
    dfPreviouslyOrdered.rename(inplace=True, columns={'Quantity':'OrderedQty'})

    dfRequirement = pd.merge(left=dfRequirement, right=dfPreviouslyOrdered, left_on=['Inventory','Variant'],
                             right_on=['Inventory','Variant'], how='left')
    
    dfRequirement['OrderedQty'] = np.where(dfRequirement['OrderedQty'].isna(), 0.0, dfRequirement['OrderedQty'])

    dfRequirement['PendignQty'] = dfRequirement['RequiredQty'] - dfRequirement['OrderedQty']

    pendingQty = float(dfRequirement['PendignQty'].sum())

    return pendingQty

def PrintPO(orderObject: models.PurchaseOrder):
    '''
    Get the data to print the PO.
    '''
    #Get the inventory table of the PO.
    poInventory = models.POInventory.objects.filter(PONumber=orderObject).values('id','Inventory','Variant','Quantity','Price','Currency')
    dfPOInventory = pd.DataFrame(poInventory)
    del poInventory

    #Get the inventory cards
    invCards = models.Inventory.objects.filter(Code__in=dfPOInventory['Inventory'].to_list())
    invCards = invCards.values('Code','Name','Unit')
    dfInventoryCards = pd.DataFrame(invCards)
    del invCards

    #Get the allocations in the po
    allocation = models.POAllocation.objects.filter(POInvId__in=dfPOInventory['id'].to_list())
    allocation = allocation.values('POInvId','WorkOrder','Quantity')
    dfAllocation = pd.DataFrame(allocation)
    del allocation

    workOrders = models.WorkOrder.objects.filter(OrderNumber__in=dfAllocation['WorkOrder'].to_list())
    workOrders = workOrders.values('OrderNumber','StyleCode','DeliveryDate')
    dfWorkOrders = pd.DataFrame(workOrders)
    del workOrders

    #merge poinventory with inventory cards to get the inventory name and unit
    dfPOInventory = pd.merge(left=dfPOInventory, right=dfInventoryCards, left_on='Inventory', right_on='Code', how='left')
    del dfInventoryCards
    dfPOInventory.drop(inplace=True, columns=['Code','Inventory'])

    #Calculate value of each entry
    dfPOInventory['Value'] = dfPOInventory['Quantity'] * dfPOInventory['Price']

    #merge allocation with work orders to get their style etc
    dfAllocation = pd.merge(left=dfAllocation, right=dfWorkOrders, left_on='WorkOrder', right_on='OrderNumber', how='left')
    del dfWorkOrders
    dfAllocation.drop(inplace=True, columns=['OrderNumber'])

    #Calculate data for summary row
    summary = {}
    summary['beforeTaxAmount'] = dfPOInventory['Value'].sum()
    summary['tax'] = (orderObject.Tax * summary['beforeTaxAmount'])/100
    summary['afterTaxAmount'] = summary['beforeTaxAmount'] + summary['tax']
    summary['Currency'] = dfPOInventory['Currency'][0]

    #Format numbers with decimals and commas
    dfPOInventory['Quantity'] = dfPOInventory['Quantity'].apply(lambda x: "{:,.2f}".format(x))
    dfPOInventory['Price'] = dfPOInventory['Price'].apply(lambda x: "{:,.2f}".format(x))
    dfPOInventory['Value'] = dfPOInventory['Value'].apply(lambda x: "{:,.2f}".format(x))
    summary['beforeTaxAmount'] = "{:,.2f}".format(summary['beforeTaxAmount'])
    summary['tax'] = "{:,.2f}".format(summary['tax'])
    summary['afterTaxAmount'] = "{:,.2f}".format(summary['afterTaxAmount'])
    
    cols = [i for i in dfPOInventory]
    poInv = [dict(zip(cols, i)) for i in dfPOInventory.values]

    cols = [i for i in dfAllocation]
    alloc = [dict(zip(cols, i)) for i in dfAllocation.values]
    
    #TODO: return POInvAlloc and POSummary as a dict or list of dicts
    return orderObject, poInv, alloc, summary