import pandas as pd

from .. import models
from . import generic_services

def GetCoreSheetList(workOrder: models.WorkOrder):
    fields = ['id', 'WorkOrder', 'NoOfPlies']
    
    if workOrder:
        cuts = models.Cut.objects.filter(WorkOrder=workOrder).values(*fields)
    else:
        cuts = models.Cut.objects.all().values(*fields)
    del workOrder
    
    if cuts:
        dfCuts = pd.DataFrame(cuts)
    else:
        dfCuts = pd.DataFrame(columns=fields)
    del cuts

    fields = ['Cut', 'Size', 'Bundle']
    bundles = models.Bundle.objects.filter(Cut__in=dfCuts['id'].to_list()).values(*fields)
    if bundles:
        dfBundles = pd.DataFrame(bundles)
    else:
        dfBundles = pd.DataFrame(columns=fields)
    del bundles, fields

    dfBundles = pd.merge(left=dfBundles, right=dfCuts, left_on='Cut', right_on='id', how='left')
    del dfCuts
    dfBundles.drop(inplace=True, columns=['id'])

    dfBundles = dfBundles.groupby('WorkOrder').agg(
        Cuts=('Cut', 'nunique'),
        Sizes=('Size', 'nunique'),
        Bundles=('Bundle', 'count'),
        Quantity=('NoOfPlies', 'sum')
    ).reset_index()
    
    return generic_services.dfToListOfDicts(dfBundles)