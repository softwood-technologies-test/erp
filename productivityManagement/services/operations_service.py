import pandas as pd
import numpy as np

from .. import models

def GetOperations (sectionFilter: str, ratePerSAM: float):
    fields = ['id','Name','Section','Category','SMV','Rate']

    if sectionFilter:
        operations = models.OperationsBank.objects.filter(Section=sectionFilter)
    else:
        operations = models.OperationsBank.objects.all()

    operations = operations.values(*fields)

    if operations:
        dfOperations = pd.DataFrame(operations)
    else:
        dfOperations = pd.DataFrame(columns=fields)
    del fields, operations
    
    dfOperations['RatePerSAM'] = dfOperations['Rate'] / dfOperations['SMV']
    sectionsMap = {
        'SP': 'Small Parts', 'F': 'Front', 'B': 'Back',
        'A1': 'Assembly 1', 'A2': 'Assembly 2', 'Fin': 'Finishing'
    }
    dfOperations['Section'] = dfOperations['Section'].map(sectionsMap).fillna(dfOperations['Section'])
    del sectionsMap
    
    maxRatePerSAM = float(dfOperations['RatePerSAM'][~np.isinf(dfOperations['RatePerSAM'])].max())
    minRatePerSAM = float(dfOperations['RatePerSAM'].min())

    if ratePerSAM:
        dfOperations = dfOperations[dfOperations['RatePerSAM'] >= ratePerSAM]

    dfOperations[['Rate', 'SMV', 'RatePerSAM']] = dfOperations[['Rate', 'SMV', 'RatePerSAM']].round(2)

    cols = [i for i in dfOperations]
    data = [dict(zip(cols, i)) for i in dfOperations.values] 
    return data, maxRatePerSAM, minRatePerSAM