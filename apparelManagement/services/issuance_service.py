import pandas as pd
import numpy as np

from django.utils.timezone import localtime

from .. import models

from .generic_services import updateModelWithDF, convertTexttoObject, concatenateValues, LOCAL_TIMEZONE

pd.options.mode.chained_assignment = None
pd.set_option('display.max_columns', None)

def AddIssuance(requisition: models.Requisition):
    issuance = {
        'Department': requisition.Department,
        'ReceivedBy': requisition.RequestBy,
        'InventoryRequisition': requisition
    }
    issuance = models.Issuance(**issuance)
    issuance.save()

    requisition.Confirmation = True
    requisition.save()

    requisitionInventories = models.RequisitionInventory.objects.filter(Requisition=requisition)
    for requisitionInventory in requisitionInventories:
        issueInventory = {
            'Issuance': issuance,
            'Inventory': requisitionInventory.Inventory,
            'Variant': requisitionInventory.Variant,
            'Quantity': requisitionInventory.Quantity
        }

        issueInventory = models.IssueInventory(**issueInventory)
        issueInventory.save()

        requisitionAllocations = models.RequisitionAllocation.objects.filter(RequisitionInventory=requisitionInventory)
        for requisitionAllocation in requisitionAllocations:
            issueAllocation = {
                'IssueInventory': issueInventory,
                'WorkOrder': requisitionAllocation.WorkOrder,
                'Quantity': requisitionAllocation.Quantity
            }
            issueAllocation = models.IssueAllocation(**issueAllocation)
            issueAllocation.save()

    return issuance.id

def GetIssuanceList (
        searchTerm: str,
        departmentFilter: str,
        issuanceNumber: int
):
    '''
    Get the list of requisitions
    '''
    if departmentFilter:
        issuances = models.Issuance.objects.filter(Department=departmentFilter)
    else:
        issuances = models.Issuance.objects.all()
    del departmentFilter

    if issuanceNumber:
        issuances = issuances.filter(id=issuanceNumber)
    
    issuances = issuances.values('id','IssuanceDate','Department','ReceivedBy','InventoryRequisition')

    if issuances:
        dfIssuances = pd.DataFrame(issuances)
    else:
        return []
    del issuances

    issuanceInventories = models.IssueInventory.objects.filter(Issuance__in=dfIssuances['id'].to_list())
    issuanceInventories = issuanceInventories.values('id','Issuance','Inventory')
    if issuanceInventories:
        dfIssuanceInventories = pd.DataFrame(issuanceInventories)
    else:
        dfIssuanceInventories = pd.DataFrame(columns=['id','Issuance','Inventory'])
    del issuanceInventories

    issuanceAllocations = models.IssueAllocation.objects.filter(IssueInventory__in=dfIssuanceInventories['id'].to_list())
    issuanceAllocations = issuanceAllocations.values('IssueInventory','WorkOrder')
    if issuanceAllocations:
        dfIssuanceAllocations = pd.DataFrame(issuanceAllocations)
    else:
        dfIssuanceAllocations = pd.DataFrame(columns=['IssueInventory','WorkOrder'])
    del issuanceAllocations

    invCards = models.Inventory.objects.filter(Code__in=dfIssuanceInventories['Inventory'].to_list()).values('Code','Name')
    if invCards:
        dfInvCards = pd.DataFrame(invCards)
    else:
        dfInvCards = pd.DataFrame(columns=['Code','Name'])
    del invCards

    dfIssuanceInventories = pd.merge(left=dfIssuanceInventories, right=dfInvCards, left_on='Inventory', right_on='Code', how='left')
    del dfInvCards
    dfIssuanceInventories.drop(inplace=True, columns=['Inventory','Code'])
    
    dfIssuanceInventories = pd.merge(left=dfIssuanceInventories, right=dfIssuanceAllocations, left_on='id', right_on='IssueInventory', how='left')
    del dfIssuanceAllocations
    dfIssuanceInventories.drop(inplace=True, columns=['id','IssueInventory'])

    dfIssuances = pd.merge(left=dfIssuances, right=dfIssuanceInventories, left_on='id', right_on='Issuance', how='left')
    del dfIssuanceInventories
    dfIssuances.drop(inplace=True, columns=['Issuance'])

    dfIssuances = dfIssuances.groupby('id').agg({
        'IssuanceDate': 'first',
        'Department': 'first',
        'ReceivedBy': 'first',
        'InventoryRequisition': 'first',
        'Name': concatenateValues,
        'WorkOrder': concatenateValues,
    }).reset_index()

    dfIssuances = dfIssuances.sort_values(by='IssuanceDate', ascending=False)

    searchTerm = searchTerm.lower()
    mask = dfIssuances.apply(lambda row: any(searchTerm in str(val).lower() for val in row.values), axis=1)
    dfIssuances = dfIssuances[mask]

    cols = [i for i in dfIssuances]
    data = [dict(zip(cols, i)) for i in dfIssuances.values]
    return data