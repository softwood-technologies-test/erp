import pandas as pd
import numpy as np

from django import forms

from .. import models, theme
from .generic_services import updateModelWithDF, convertTexttoObject, concatenateValues
from .auth_service import canApprovePD

pd.options.mode.chained_assignment = None
pd.set_option('display.max_columns', None)

#Blank form to add data of purchase demand
class PurchaseDemandForm (forms.Form):
    Demandee = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=False,
    )

#Blank form to create inventories of purchase demand
class PurchaseDemandInventoryForm (forms.Form):
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

def GetPurchaseDemandList (
    searchTerm: str,
    department: str,
    pdNumber: int,
    statusFilter: str
):
    '''
    Get the list of all purchase orders
    '''
    demands = models.PurchaseDemand.objects.all()
    
    demands = demands.values('id','DemandDate','Department','Demandee','Approval','PONumber')
    
    if demands:
        dfDemands = pd.DataFrame(demands)
        del demands
    else:
        return []
    
    inventories = models.PDInventory.objects.filter(PDNumber__in=dfDemands['id'].to_list())
    inventories = inventories.values('id','PDNumber','Inventory')
    dfInventories = pd.DataFrame(inventories)
    del inventories

    inventoryCards = models.Inventory.objects.filter(Code__in=dfInventories['Inventory'].to_list())
    inventoryCards = inventoryCards.values('Code','Name')
    dfInventoryCards = pd.DataFrame(inventoryCards)
    del inventoryCards
    
    if department:
        dfDemands = dfDemands[dfDemands['Department']==department]
    if pdNumber:
        dfDemands = dfDemands[dfDemands['id'] == int(pdNumber)]
    if statusFilter:
        match statusFilter:
            case 'OnApp':
                dfDemands = dfDemands[dfDemands['Approval'].isna()]
            case 'OnPO':
                dfDemands = dfDemands[(dfDemands['Approval'].astype(bool) == True) & (dfDemands['PONumber'].isna())]
            case 'Rej':
                dfDemands['Temp'] = dfDemands['Approval'].map(lambda x: 'True' if x is None else x)
                dfDemands = dfDemands[dfDemands['Temp'].astype(bool) == False]
                dfDemands.drop(inplace=True, columns=['Temp'])
            case 'Close':  
                dfDemands['Temp'] = dfDemands['Approval'].map(lambda x: 'True' if x is None else x)
                dfTemp1 = dfDemands[dfDemands['Temp'].astype(bool) == False]
                dfDemands.drop(inplace=True, columns=['Temp'])

                dfTemp2 = dfDemands[dfDemands['Approval'].astype(bool)]
                dfTemp2 = dfTemp2[~dfTemp2['PONumber'].isna()]

                dfDemands = pd.concat([dfTemp1, dfTemp2])
                del dfTemp1, dfTemp2
            case _:
                raise ValueError('Invalid Input')
    if dfDemands.empty:
        return []

    #Give verbose name to the id column
    dfDemands.rename(inplace=True, columns={'id':'PDNumber'})

    dfDemands = pd.merge(left=dfDemands, right=dfInventories, left_on='PDNumber', right_on='PDNumber', how='left')
    del dfInventories

    dfDemands = pd.merge(left=dfDemands, right=dfInventoryCards, left_on='Inventory', right_on='Code', how='left')
    dfDemands.drop(inplace=True, columns=['Inventory','Code'])
    del dfInventoryCards

    #Concate rows who have same Inventory Name in common
    dfDemands = dfDemands.groupby('PDNumber').agg({
        'DemandDate': 'first',
        'Department': 'first',
        'Demandee': 'first',
        'Approval': 'first',
        'PONumber': 'first',
        'Name': concatenateValues,
    }).reset_index()

    map = {True: 'Approved', False: 'Rejected', None: 'Pending'}
    dfDemands['Approval'] = dfDemands['Approval'].map(map)

    searchTerm = searchTerm.lower()
    mask = dfDemands.apply(lambda row: any(searchTerm in str(val).lower() for val in row.values), axis=1)
    dfDemands = dfDemands[mask]

    dfDemands = dfDemands.sort_values(by='PDNumber', ascending=False)

    cols = [i for i in dfDemands]
    data = [dict(zip(cols, i)) for i in dfDemands.values]
    return data

def AddPurchaseDemand(
        dfDemand: pd.DataFrame,
        dfInventory: pd.DataFrame,
) -> int:
    '''Save a new PD'''

    #Get the department
    department = dfDemand['Department'][0]
    #Return error is department is blank
    if(department == '') or (dfDemand['Department'].isna().all()):
        raise ValueError ('No department is Provided')
    
    demandee = dfDemand['Demandee'][0]
    if demandee == '':
        raise ValueError ('No name is Provided')
    
    dfInventory = dfInventory[dfInventory['InvCode'].str.len() > 0]
    if dfInventory.empty:
        raise ValueError ('Please select an inventory')
    
    dfDemand['Department'] = convertTexttoObject(models.Department, dfDemand['Department'], 'Name')
    
    purchaseDemand = {
        'Department': dfDemand['Department'][0],
        'Demandee': dfDemand['Demandee'][0],
        'ApprovedBy': None,
        'PONumber': None,
        'Approval': None
    }
    try:
        purchaseDemand = models.PurchaseDemand(**purchaseDemand)
        purchaseDemand.save()
    except Exception as e:
        raise ValueError(f"Error saving Demand: {e}")
    
    dfInventory['Currency'] = np.where(dfInventory['Currency'].str.len() == 0, 'PKR', dfInventory['Currency'])
    dfInventory['Forex'] = np.where(dfInventory['Forex'].str.len() == 0, 1, dfInventory['Forex'])

    dfInventory['Inventory'] = convertTexttoObject(models.Inventory, dfInventory['InvCode'], 'Code')
    dfInventory.drop(inplace=True, columns=['InvCode'])

    dfInventory['Currency'] = convertTexttoObject(models.Currency, dfInventory['Currency'], 'Code')

    dfInventory['PDNumber'] = purchaseDemand    

    for _, row in dfInventory.iterrows():
        newEntry = models.PDInventory(**row.to_dict())
        newEntry.save()

    return purchaseDemand.id

def EditPurchaseDemand(
        purchaseDemand: models.PurchaseDemand,
        dfDemand: pd.DataFrame,
        dfPDInventory: pd.DataFrame
) -> None:
    #Get the department
    department = dfDemand['Department'][0]
    #Return error is department is blank
    if(department == '') or (dfDemand['Department'].isna().all()):
        raise ValueError ('No department is Provided')
    
    demandee = dfDemand['Demandee'][0]
    if demandee == '':
        raise ValueError ('No name is Provided')
    
    dfPDInventory = dfPDInventory.replace('null', '')
    dfPDInventory = dfPDInventory[dfPDInventory['InvCode'].str.len() > 0]
    if dfPDInventory.empty:
        raise ValueError ('Please select an inventory')
    
    previousInventores = models.PDInventory.objects.filter(PDNumber=purchaseDemand).values('id','Inventory','Variant')
    if previousInventores:
        dfPrevioiusInventories = pd.DataFrame(previousInventores)
    else:
        dfPrevioiusInventories = pd.DataFrame(columns=['id','Inventory','Variant'])
    del previousInventores
    
    dfDemand['DemandDate'] = pd.to_datetime(dfDemand["DemandDate"], format="%d/%m/%Y")

    dfDemand['Department'] = convertTexttoObject(models.Department, dfDemand['Department'], 'Name')

    purchaseDemand.DemandDate = dfDemand['DemandDate'][0]
    purchaseDemand.Department = dfDemand['Department'][0]
    purchaseDemand.Demandee = dfDemand['Demandee'][0]
    purchaseDemand.ApprovedBy = None
    purchaseDemand.PONumber = None
    purchaseDemand.Approval = None
    purchaseDemand.save()

    dfPDInventory.rename(inplace=True, columns={'InvCode':'Inventory'})
    dfPDInventory = pd.merge(left=dfPDInventory, right=dfPrevioiusInventories, left_on=['Inventory','Variant'],
                             right_on=['Inventory','Variant'], how='left')    

    dfPDInventory['Currency'] = np.where(dfPDInventory['Currency'].str.len() == 0, 'PKR', dfPDInventory['Currency'])
    dfPDInventory['Forex'] = np.where(dfPDInventory['Forex'].str.len() == 0, 1, dfPDInventory['Forex'])

    dfPDInventory['Inventory'] = convertTexttoObject(models.Inventory, dfPDInventory['Inventory'], 'Code')

    dfPDInventory['Currency'] = convertTexttoObject(models.Currency, dfPDInventory['Currency'], 'Code')

    dfPDInventory['PDNumber'] = purchaseDemand 

    try:
        updateModelWithDF(models.PDInventory, dfPDInventory, dfPrevioiusInventories)
    except Exception as e:
        raise ValueError(e)

def ProcessDemandData(purchaseDemand: models.PurchaseDemand):
    demand = {
        'DemandNumber': purchaseDemand.id,
        'DemandDate': purchaseDemand.DemandDate,
        'Department': purchaseDemand.Department.Name,
        'Demandee': purchaseDemand.Demandee,
        'ApprovedBy': purchaseDemand.ApprovedBy,
        'PONumber': purchaseDemand.PONumber,
    }

    if not demand['ApprovedBy']:
        demand['ApprovedBy'] = ''
    
    if not demand['PONumber']:
        demand['PONumber'] = ''

    inventories = models.PDInventory.objects.filter(PDNumber=purchaseDemand)
    inventories = inventories.values('Inventory','Variant','Quantity','Price','Currency','Forex')

    return demand, inventories

def GetDataForPDApproval (demand: models.PurchaseDemand):
    if not demand.Approval == None:
        raise ValueError ('This resource is closed')
    
    inventories = models.PDInventory.objects.filter(PDNumber=demand).values('Inventory','Variant','Quantity','Price','Currency')
    dfInventories = pd.DataFrame(inventories)
    del inventories

    inventoryCards = models.Inventory.objects.filter(Code__in = dfInventories['Inventory'].to_list())
    inventoryCards = inventoryCards.values('Code','Name','Unit')
    dfInventoryCards = pd.DataFrame(inventoryCards)
    del inventoryCards
    
    demandDict = {
        'Department': demand.Department.FullName,
        'Demandee': demand.Demandee,
    }
    del demand
    dfDemand = pd.DataFrame(demandDict, index=[0])
    del demandDict

    dfInventories = pd.merge(left=dfInventories, right=dfInventoryCards, left_on='Inventory', right_on='Code', how='left')
    dfInventories.drop(inplace=True, columns=['Inventory','Code'])

    dfInventories['Value'] = dfInventories['Quantity'] * dfInventories['Price']

    dfInventories['Name'] = dfInventories['Name']+ ' ' + dfInventories['Variant']+ ' (' + dfInventories['Quantity'].astype(str) + ' '+dfInventories['Unit']+')'
    dfInventories.drop(inplace=True, columns=['Quantity','Price','Variant','Unit'])

    dfInventories = dfInventories.groupby(lambda x: 'all').agg({
        'Name': concatenateValues,
        'Currency': 'first',
        'Value': 'sum',
    }).reset_index()

    dfInventories['Value'] = dfInventories['Currency']+'. '+dfInventories['Value'].astype(str)+'/-'
    dfInventories.drop(inplace=True, columns=['Currency'])
    
    dfDemand['Details'] = dfInventories['Name'][0]
    dfDemand['Value'] = dfInventories['Value'][0]

    data = dfDemand.iloc[0].to_dict()

    data['Description'] = f"Request by {data['Demandee']} from {data['Department']} for {data['Details']} with value of {data['Value']}"

    #Get context for the PD and return it

    #print(data)
    return data, None

def ApprovePD (request, demand: models.PurchaseDemand, approval: str):
    if not canApprovePD(request, demand):
        raise PermissionError('Not Allowed')

    if approval == 'None':
        return
    elif approval == 'true':
        approval = True
    else:
        approval = False

    demand.Approval = approval
    demand.ApprovedBy = request.user

    demand.save()
    return

def ConvertPDtoPO (demand: models.PurchaseDemand, supplier: str) -> int:
    '''
    Convert a PD to PO and return the PO Number
    '''
    if (demand.PONumber) or (not demand.Approval):
        raise ValueError('This demand is already closed')
    
    if (supplier == 'None') or (supplier == 'null'):
        raise ValueError('No Supplier is selected')     

    try:
        supplier = models.Supplier.objects.get(Name=supplier)
    except Exception as e:
        raise LookupError(e)
    
    inventories = models.PDInventory.objects.filter(PDNumber = demand).values('Inventory','Variant','Quantity','Price','Currency','Forex')
    dfInventories = pd.DataFrame(inventories)
    del inventories

    orderCard = {
        'DeliveryDate': demand.DemandDate,
        'Supplier': supplier,
        'Tax': 0.0
    }

    orderCard = models.PurchaseOrder (**orderCard)
    orderCard.save()
    
    dfInventories['Inventory'] = convertTexttoObject(models.Inventory, dfInventories['Inventory'], 'Code')
    dfInventories['Currency'] = convertTexttoObject(models.Currency, dfInventories['Currency'], 'Code')

    dfInventories['PONumber'] = orderCard

    for _, row in dfInventories.iterrows():
        newEntry = models.POInventory(**row.to_dict())
        newEntry.save()
    
    demand.PONumber = orderCard
    demand.save()

    return orderCard.id