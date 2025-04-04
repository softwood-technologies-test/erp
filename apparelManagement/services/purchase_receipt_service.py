import pandas as pd
import numpy as np

from django import forms

from .. import models, theme
from .generic_services import updateModelWithDF, convertTexttoObject, concatenateValues

pd.options.mode.chained_assignment = None
pd.set_option('display.max_columns', None)

#Blank form to add data of purchase receipt
class PurchaseReceiptForm(forms.Form):
    Invoice = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=False,
    )

    Vehicle = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=False,
    )

    Bilty = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=True,
    )
    
    BiltyValue = forms.FloatField(
        widget=forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=True,
        initial=0,
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

def GetReceiptList(searchTerm: str, supplier: str, receiptNumber: int):
    '''
    Get the list of all purchase orders
    '''
    if receiptNumber:
        receipts = models.InventoryReciept.objects.filter(id=receiptNumber).values('id','ReceiptDate','Supplier','PONumber')
    elif supplier:
        receipts = models.InventoryReciept.objects.filter(Supplier=supplier).values('id','ReceiptDate','Supplier','PONumber')
    else:
        receipts = models.InventoryReciept.objects.all().values('id','ReceiptDate','Supplier','PONumber')
    dfReceipts = pd.DataFrame(receipts)
    del receipts

    if dfReceipts.empty:
        return []
    
    inventories = models.RecInventory.objects.filter(ReceiptNumber__in=dfReceipts['id'].to_list())
    inventories = inventories.values('id','ReceiptNumber','InventoryCode')
    dfInventories = pd.DataFrame(inventories)
    del inventories

    allocations = models.RecAllocation.objects.filter(RecInvId__in=dfInventories['id'].to_list())
    allocations = allocations.values('RecInvId','WorkOrder')
    dfAllocations = pd.DataFrame(allocations)
    del allocations

    inventoryCards = models.Inventory.objects.filter(Code__in=dfInventories['InventoryCode'].to_list())
    inventoryCards = inventoryCards.values('Code','Name')
    dfInventoryCards = pd.DataFrame(inventoryCards)
    del inventoryCards

    #Give verbose names to the id columns
    dfReceipts.rename(inplace=True, columns={'id':'ReceiptNumber'})
    dfInventories.rename(inplace=True, columns={'id':'RecInvId'})

    dfReceipts = pd.merge(left=dfReceipts, right=dfInventories, left_on='ReceiptNumber', right_on='ReceiptNumber', how='left')
    del dfInventories

    dfReceipts = pd.merge(left=dfReceipts, right=dfAllocations, left_on='RecInvId', right_on='RecInvId', how='left')
    dfReceipts.drop(inplace=True, columns=['RecInvId'])
    del dfAllocations

    dfReceipts = pd.merge(left=dfReceipts, right=dfInventoryCards, left_on='InventoryCode', right_on='Code', how='left')
    dfReceipts.drop(inplace=True, columns=['InventoryCode','Code'])
    del dfInventoryCards

    #Convert work order float to string, without decimals
    dfReceipts['WorkOrder'] = np.where(dfReceipts['WorkOrder'].isna(), 0, dfReceipts['WorkOrder'])
    dfReceipts['WorkOrder'] = dfReceipts['WorkOrder'].astype(int).astype(str)
    dfReceipts['WorkOrder'] = np.where(dfReceipts['WorkOrder']=='0', '', dfReceipts['WorkOrder'])

    #Concate rows who have same PO number in common
    dfReceipts = dfReceipts.groupby('ReceiptNumber').agg({
        'ReceiptDate': 'first',
        'Supplier': 'first',
        'PONumber': 'first',
        'Name': concatenateValues,
        'WorkOrder': concatenateValues,
    }).reset_index()

    searchTerm = searchTerm.lower()
    mask = dfReceipts.apply(lambda row: any(searchTerm in str(val).lower() for val in row.values), axis=1)
    dfReceipts = dfReceipts[mask]

    dfReceipts = dfReceipts.sort_values(by='ReceiptNumber', ascending=False)

    cols = [i for i in dfReceipts]
    data = [dict(zip(cols, i)) for i in dfReceipts.values]
    return data

def GetPOData(purchaseOrder: models.PurchaseOrder):
    poInventories = models.POInventory.objects.filter(PONumber=purchaseOrder).values('Inventory','Variant','Quantity')
    if poInventories:
        dfPOInventories = pd.DataFrame(poInventories)
    else:
        dfPOInventories = pd.DataFrame(columns=['Inventory','Variant','Quantity'])
    del poInventories

    inventories = models.Inventory.objects.filter(Code__in=dfPOInventories['Inventory'].to_list()).values('Code','Name')
    if inventories:
        dfInventories = pd.DataFrame(inventories)
    else:
        dfInventories = pd.DataFrame(columns=['Code','Name'])
    del inventories

    dfPOInventories = pd.merge(left=dfPOInventories, right=dfInventories, left_on='Inventory', right_on='Code', how='left')
    del dfInventories
    dfPOInventories.drop(inplace=True, columns=['Code'])

    dfPOInventories['Name'] = dfPOInventories['Inventory'].astype(str)+' - '+dfPOInventories['Name'].astype(str)
    
    cols = [i for i in dfPOInventories]
    data = [dict(zip(cols, i)) for i in dfPOInventories.values]
    return data

def AddPurchaseReceipt(dfReceipt:pd.DataFrame, dfRecInventories:pd.DataFrame):
    '''
    Add the receipt from new receipt Form
    '''
    purchaseOrder = dfReceipt['PONumber'][0]
    purchaseOrder = models.PurchaseOrder.objects.get(id=purchaseOrder)

    poInventories = models.POInventory.objects.filter(PONumber=purchaseOrder).values('id','Inventory','Variant')
    dfPOInventories = pd.DataFrame(poInventories)
    del poInventories

    poAllocations = models.POAllocation.objects.filter(POInvId__in=dfPOInventories['id'].to_list())
    poAllocations = poAllocations.values('POInvId','WorkOrder','Quantity')
    dfPOAllocation = pd.DataFrame(poAllocations)
    del poAllocations

    invReceipt = {
        'Invoice':dfReceipt['Invoice'][0],
        'Supplier':purchaseOrder.Supplier,
        'Vehicle':dfReceipt['Vehicle'][0],
        'Bilty':dfReceipt['Bilty'][0],
        'BiltyValue':dfReceipt['BiltyValue'][0],
        'PONumber':purchaseOrder,
    }

    if dfRecInventories.empty:
        raise ValueError('No Inventory provided')

    receiptCard = models.InventoryReciept(**invReceipt)
    receiptCard.save()

    dfRecInventories = dfRecInventories.replace('null', '')  

    dfRecInventories['Quantity'] = dfRecInventories['Quantity'].astype(float)

    dfPOInventories.rename(inplace=True, columns={'id':'POInvId', 'Inventory':'InvCode'})

    dfRecInventories = pd.merge(left=dfRecInventories, right=dfPOInventories, left_on=['InvCode','Variant'],
                                right_on=['InvCode','Variant'], how='left')
    
    # Adjust order-wise allocations for where received qty is less than allocated qty.
    if not dfPOAllocation.empty:
        for index, row in dfRecInventories.iterrows():
            #Get the allocations associated with the inventory
            temp = dfPOAllocation[dfPOAllocation['POInvId']==row['POInvId']]
            allocatedQty = temp['Quantity'].sum()
            del temp
            
            receivedQty = row['Quantity']   
                
            if allocatedQty > receivedQty:
                factor = receivedQty/allocatedQty
                dfPOAllocation['Quantity'] = np.where(dfPOAllocation['POInvId']==row['POInvId'],
                                                    dfPOAllocation['Quantity']*factor, dfPOAllocation['Quantity'])
                
        dfPOAllocation = pd.merge(left=dfPOAllocation,right=dfPOInventories, left_on='POInvId', right_on='POInvId', how='left')
        
        dfRecAllocation = dfPOAllocation[['WorkOrder','Quantity','InvCode','Variant']]
    else:
        dfRecAllocation = pd.DataFrame(columns=['WorkOrder','Quantity','InvCode','Variant'])
    del dfPOAllocation, dfPOInventories
    dfRecInventories.drop(inplace=True, columns=['POInvId'])

    dfRecInventories['ReceiptNumber'] = receiptCard
    dfRecInventories['Approval'] = False
    dfRecInventories['QualityComments'] = None

    temp = dfRecInventories.drop(columns=['Quantity','ReceiptNumber','Approval','QualityComments'])
    temp['id'] = None

    InventoryObjs = [models.Inventory.objects.get(Code=row['InvCode']) for index, row in dfRecInventories.iterrows()]
    dfRecInventories['InventoryCode'] = InventoryObjs
    dfRecInventories.drop(inplace=True, columns=['InvCode'])

    for index, row in dfRecInventories.iterrows():
        try:
            newEntry = models.RecInventory(**row.to_dict())
            newEntry.save()
            temp.loc[index,'id'] = newEntry
        except Exception as e:
            raise ValueError(f"Cannot save at {index}: {e}")
    dfRecInventories = temp
    del temp

    dfRecAllocation = pd.merge(left=dfRecAllocation, right=dfRecInventories, left_on=['InvCode','Variant'],
                               right_on=['InvCode','Variant'], how='left')
    del dfRecInventories

    dfRecAllocation.drop(inplace=True, columns=['InvCode','Variant'])
    dfRecAllocation.rename(inplace=True, columns={'id':'RecInvId'})

    WorkOrderObjs = [models.WorkOrder.objects.get(OrderNumber=row['WorkOrder']) for index, row in dfRecAllocation.iterrows()]
    dfRecAllocation['WorkOrder'] = WorkOrderObjs

    for index, row in dfRecAllocation.iterrows():
        try:
            newEntry = models.RecAllocation(**row.to_dict())
            newEntry.save()
        except Exception as e:
            raise ValueError(f"Cannot save at {index}: {e}")

    return receiptCard.id

def EditPurchaseReceipt (
        receiptObject: models.InventoryReciept, 
        dfReceipt: pd.DataFrame,
        dfRecInventory: pd.DataFrame,
        dfRecAllocation: pd.DataFrame
):
    '''
    Update the Receipt from the data in the Receipt table.
    '''
    #Set order details to correct format/objects
    SupplierObjs = [models.Supplier.objects.get(Name=row['Supplier']) for _, row in dfReceipt.iterrows()]
    dfReceipt['Supplier'] = SupplierObjs

    try:
        dfReceipt['BiltyValue'] = dfReceipt['BiltyValue'].astype(float)
    except:
        dfReceipt['BiltyValue'] = 0.0

    #Update order object to as provided by user and save it.
    receiptObject.Invoice = dfReceipt['Invoice'][0]
    receiptObject.Vehicle = dfReceipt['Vehicle'][0]
    receiptObject.Supplier = dfReceipt['Supplier'][0]
    receiptObject.Bilty = dfReceipt['Bilty'][0]
    receiptObject.BiltyValue = dfReceipt['BiltyValue'][0]
    receiptObject.save()

    dfRecInventory = dfRecInventory.replace('null', '')

    #Get the already saved inventories against this PO and their allocation
    previousInventories = models.RecInventory.objects.filter(ReceiptNumber=receiptObject).values('id','InventoryCode','Variant')
    dfPreviousInventories = pd.DataFrame(previousInventories)
    del previousInventories

    dfRecInventory['Quantity'] = np.where(dfRecInventory['Quantity'].str.len()==0, 0, dfRecInventory['Quantity'])
    dfRecInventory['Quantity'] = dfRecInventory['Quantity'].astype(float)

    if dfRecInventory.empty:
        raise ValueError('No Inventory provided')
    
    dfRecInventory = pd.merge(left=dfRecInventory, right=dfPreviousInventories, left_on=['InvCode','Variant'],
                           right_on=['InventoryCode','Variant'], how='left')
    dfRecInventory.drop(inplace=True, columns=['InventoryCode'])

    InventoryObjs = [models.Inventory.objects.get(Code=row['InvCode']) for _, row in dfRecInventory.iterrows()]
    dfRecInventory['InvCode'] = InventoryObjs

    dfRecInventory.rename(inplace=True, columns={'InvCode':'InventoryCode'})

    dfRecInventory['ReceiptNumber'] = receiptObject

    try:
        updateModelWithDF(targetTable=models.RecInventory, newData=dfRecInventory, previousData=dfPreviousInventories)
    except Exception as e:
        raise ValueError(e)
    
    dfRecAllocation = dfRecAllocation.replace('null', '')
    #Remove empty rows from allocation
    dfRecAllocation = dfRecAllocation[dfRecAllocation['WorkOrder'] !='']

    #The inventory code on which the allocation is made
    allocationInvVariant = str(dfReceipt['allocationInvCode'][0]).split('_')

    dfRecAllocation = dfRecAllocation[~dfRecAllocation['WorkOrder'].isna()]

    #Save the allocation if it is provided
    if not dfRecAllocation.empty:        
        dfRecAllocation['WorkOrder'] = dfRecAllocation['WorkOrder'].astype(int)
        try:
            receiptInvObj = models.RecInventory.objects.get(ReceiptNumber=receiptObject, InventoryCode=allocationInvVariant[0], Variant=allocationInvVariant[1])
            dfRecAllocation['RecInvId'] = receiptInvObj
        except Exception as e:
            raise ValueError(e)
        
        previousAllocations = models.RecAllocation.objects.filter(RecInvId=receiptInvObj).values('id','WorkOrder')
        dfPreviousAllocations = pd.DataFrame(previousAllocations)
        del previousAllocations

        if dfPreviousAllocations.empty:
            dfRecAllocation['id'] = None
        else:
            dfRecAllocation = pd.merge(left=dfRecAllocation, right=dfPreviousAllocations, left_on='WorkOrder', right_on='WorkOrder', how='left')
        
        OrderObjs = [models.WorkOrder.objects.get(OrderNumber=row['WorkOrder']) for index, row in dfRecAllocation.iterrows()]
        dfRecAllocation['WorkOrder'] = OrderObjs

        try:
            updateModelWithDF(targetTable=models.RecAllocation, newData=dfRecAllocation, previousData=dfPreviousAllocations)
        except Exception as e:
            raise ValueError (e)        

def ProcessReceiptData(receiptObject: models.InventoryReciept):
    '''
    Get the data of the provided Receipt.
    '''
    receipt = {
        'ReceiptNo': receiptObject.id,
        'PONumber': receiptObject.PONumber.id,
        'RecieptDate': receiptObject.ReceiptDate,
        'Invoice':receiptObject.Invoice,
        'Supplier': receiptObject.Supplier.Name,
        'Vehicle': receiptObject.Vehicle,
        'Bilty': receiptObject.Bilty,
        'BiltyValue': receiptObject.BiltyValue,
        'PONumber': receiptObject.PONumber,
    }

    inventories = models.RecInventory.objects.filter(ReceiptNumber=receiptObject)
    inventories = inventories.values('id','InventoryCode','Variant','Quantity','Approval','QualityComments')

    #Replace any None values with blank
    for item in inventories:
        for key, value in item.items():
            item[key] = '' if value is None else value
    
    return receipt, inventories

def GetReceiptAllocation(inventoryCode: str, variant: str, urlPath: str):
    '''
    Get the allocation of an inventory code in a provided Receipt.
    '''
    urlParts = urlPath.strip('/').split('/')
    del urlPath

    if len(urlParts) == 2:
        #This is true for a new receipts and there would be no allocation
        return
    elif len(urlParts) == 3:
        receiptNumber = int(urlParts[1])
        receiptObject = models.InventoryReciept.objects.get(id=receiptNumber)

        receiptInventory = models.RecInventory.objects.get(ReceiptNumber=receiptObject, InventoryCode=inventoryCode, Variant=variant)
        
        allocation = models.RecAllocation.objects.filter(RecInvId=receiptInventory)
        allocation = allocation.values('WorkOrder','Quantity')

        if allocation:
            return list(allocation)
        else:
            return None
    else:
        raise SyntaxError('Invalid Input')

    