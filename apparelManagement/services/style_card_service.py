import pandas as pd
import numpy as np

from django import forms

from .. import models, theme
from .generic_services import convertTexttoObject, updateModelWithDF

pd.options.mode.chained_assignment = None

class StyleForm (forms.Form):
    StyleCode = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=True,
    )
    
    StyleName = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=True,
    )

    Notes = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        required=True,
    )

class StyleVariantForm (forms.Form):
    Variant1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        max_length=255,
        required=False,
    )
    Variant2 = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        max_length=255,
        required=False,
    )

class StyleConsForm(forms.Form):
    Consumption = forms.FloatField (
        widget=forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=False,
    )

    SizeDetails = forms.CharField(
        widget=forms.TextInput(attrs={'class': theme.theme['textInput']}),
        max_length=255,
        required=False,
    )

class StyleRouteForm (forms.Form):
    Sequence = forms.IntegerField(
        widget = forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=False,
        initial=1,
    )

class StitchOBForm (forms.Form):
    Sequence = forms.IntegerField(
        widget = forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=False,
        initial=1,
    )

class FinishOBForm (forms.Form):
    Sequence = forms.IntegerField(
        widget = forms.NumberInput(attrs={'class': theme.theme['textInput']}),
        required=False,
        initial=1,
    )

def getStyleCard (searchTerm, customer):
    if customer:
        Styles = models.StyleCard.objects.filter(Customer=customer).values()
    else:
        Styles = models.StyleCard.objects.all().values()

    df_style = pd.DataFrame(Styles)
    searchTerm = searchTerm.lower()

    mask = df_style.apply(lambda row: any(searchTerm in str(val).lower() for val in row.values)
                        , axis=1)

    df_style = df_style[mask]

    if not df_style.empty:
        df_style = df_style.sort_values (by='StyleCode')
        df_style = df_style.sort_values (by='Customer_id')

    cols = [i for i in df_style]
    df_style = [dict(zip(cols, i)) for i in df_style.values]
    return df_style

def calculateFinalConsumption(dfConsumption: pd.DataFrame) -> pd.Series:
    inventories = models.Inventory.objects.filter(Code__in=dfConsumption['InventoryCode'].to_list())
    inventories = inventories.values('Code','Unit')
    if inventories:
        dfConsInventories = pd.DataFrame(inventories)
    else:
        dfConsInventories = pd.DataFrame(columns=['Code','Unit'])
    del inventories

    invUnits = models.Unit.objects.filter(Name__in=dfConsInventories['Unit'].to_list())
    invUnits = invUnits.values('Name','Group','Factor')
    if invUnits:
        dfInvUnits = pd.DataFrame(invUnits)
    else:
        dfInvUnits = pd.DataFrame(columns=['Name','Group','Factor'])
    del invUnits

    consUnits = models.Unit.objects.filter(Name__in=dfConsumption['Unit'].to_list())
    consUnits = consUnits.values('Name','Group','Factor')
    if consUnits:
        dfConsUnits = pd.DataFrame(consUnits)
    else:
        dfConsUnits = pd.DataFrame(columns=['Name','Group','Factor'])
    del consUnits

    dfConsumption = pd.merge(left=dfConsumption, right=dfConsUnits, left_on='Unit', right_on='Name', how='left')
    del dfConsUnits
    dfConsumption.drop(inplace=True, columns=['Name'])
    dfConsumption.rename(inplace=True, columns={'Group':'ConsUnitGroup','Factor':'ConsUnitFactor'})

    dfConsInventories = pd.merge(left=dfConsInventories, right=dfInvUnits, left_on='Unit', right_on='Name', how='left')
    del dfInvUnits
    dfConsInventories.drop(inplace=True, columns=['Name'])
    dfConsInventories.rename(inplace=True, columns={'Unit':'InvUnit','Group':'InvUnitGroup','Factor':'InvUnitFactor'})

    dfConsumption = pd.merge(left=dfConsumption, right=dfConsInventories, left_on='InventoryCode', right_on='Code', how='left')
    del dfConsInventories
    dfConsumption.drop(inplace=True, columns=['Code'])
    dfConsumption.rename(inplace=True, columns={'Unit_x':'Unit'})

    if (flagColGroupMismatch(dfConsumption[['ConsUnitGroup','InvUnitGroup']])):
        raise ValueError('Incorrect Consumption Unit')
    
    dfConsumption.drop(inplace=True, columns=['ConsUnitGroup','InvUnitGroup','InvUnit'])

    dfConsumption['ConsUnitFactor'] = np.where(dfConsumption['ConsUnitFactor'].isna(), 1.0, dfConsumption['ConsUnitFactor'])

    dfConsumption['Consumption'] = dfConsumption['Consumption'].astype(float)

    dfConsumption['FinalCons'] = dfConsumption['Consumption'] * dfConsumption['InvUnitFactor'] * dfConsumption['ConsUnitFactor']    

    return dfConsumption['FinalCons']

def flagColGroupMismatch(df: pd.DataFrame) -> bool:
    flag = (df['ConsUnitGroup'].notna()) & (df['InvUnitGroup'].notna()) & (df['ConsUnitGroup'] != df['InvUnitGroup'])

    return flag.any()

def AddStyleCard(
        dfStyle: pd.DataFrame,
        dfVariants: pd.DataFrame,
        dfRoute: pd.DataFrame,
        ) -> str:
    '''Save a new style Card'''
    #Get the style code
    styleCode = dfStyle['StyleCode'][0]
    #Return error is style code is blank
    if(styleCode == ''):
        raise ValueError ('No Style Code is Provided')
    
    #Replace any blank variants with Nan
    dfVariants = dfVariants.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    dfVariants['Variant1'] = np.where(dfVariants['Variant1'].str.len()==0,np.nan, dfVariants['Variant1'])
    dfVariants['Variant2'] = np.where(dfVariants['Variant2'].str.len()==0,np.nan, dfVariants['Variant2'])
    dfVariants = dfVariants[~dfVariants.isnull().all(axis=1)]

    #Raise error if no variants are provided
    if dfVariants.empty:
        raise ValueError('No Variant is provided')

    if dfRoute['type'].str.len().sum() == 0:
        raise ValueError('No Production route is provided')
    
    #Convert Customer to model objects and assign to style
    dfStyle['Customer'] = convertTexttoObject(models.Customer, dfStyle['Customer'],'Name')
    
    #Create dict from the provided data, to be able to save in database
    styleCard = {
        'StyleCode': dfStyle['StyleCode'][0],
        'StyleName': dfStyle['StyleName'][0],
        'Customer': dfStyle['Customer'][0],
        'Category': dfStyle['Category'][0],
        'Notes': dfStyle['Notes'][0],
        }
    
    try:
        #Try to fetch style and if found, raise error
        models.StyleCard.objects.get(StyleCode=styleCard['StyleCode'])    
        raise ValueError(f"StyleCard with StyleCode: {styleCard['StyleCode']}, already exists.")
    except models.StyleCard.DoesNotExist:
        #Create a new style Card if it is not found already
        styleCard = models.StyleCard(**styleCard)
        styleCard.save()
    except Exception as e:
        #Raise any other error, if found to be safe.
        raise LookupError(f"Error saving style card: {e}") 

    #Create a Variant1 DF from main DF and remove blanks
    dfVariants1 = dfVariants['Variant1'].dropna().to_frame()

    #Create a Variant2 DF from main DF and remove blanks
    dfVariants2 = dfVariants['Variant2'].dropna().to_frame()

    #Cross Join Varian1 and Variant2 DFs.
    dfVariants = pd.merge(left=dfVariants1, right=dfVariants2, how="cross")
    #If dfVariants is still empty, it means that there is only one column of variants. Set it to which one is non-empty
    if dfVariants.empty:
        dfVariants = dfVariants2 if dfVariants1.empty else dfVariants1
    del dfVariants1, dfVariants2

    dfVariants['Style'] = styleCard

    dfVariants['VariantCode'] = dfVariants['Variant1']+'-'+dfVariants['Variant2']
    dfVariants.drop(inplace=True, columns=['Variant1','Variant2'])

    for _, row in dfVariants.iterrows():
        newEntry = models.StyleVariant(**row.to_dict())
        newEntry.save()

    if not dfRoute.empty:
        if dfRoute['Sequence'].duplicated().any():
            raise ValueError('Incorrect Sequence is Provided')
    
        dfRoute['Style'] = styleCard
        dfRoute['Cost'] = 0.0
        
        dfRoute.rename(inplace=True, columns={'type':'Stage'})

        for _, row in dfRoute.iterrows():
            newEntry = models.StyleRoute(**row.to_dict())
            newEntry.save()

    return styleCard.StyleCode

def UpdateStyleCard(
        dfStyle: pd.DataFrame,
        dfVariants: pd.DataFrame,
        dfConsumption: pd.DataFrame,
        dfRoute: pd.DataFrame,
        ) -> None:
    '''Edit the style card based on the updated data'''
    
    #Return error is style code is blank
    if(dfStyle['StyleCode'][0] == ''):
        raise ValueError ('No Style Code is Provided')
    dfStyle['Customer'] = convertTexttoObject(models.Customer, dfStyle['Customer'], 'Name')

    #Create dict from the provided data, to be able to save in database
    styleCard = {
        'StyleCode': dfStyle['StyleCode'][0],
        'StyleName': dfStyle['StyleName'][0],
        'Customer': dfStyle['Customer'][0],
        'Category': dfStyle['Category'][0],
        'Notes': dfStyle['Notes'][0],
        }
    del dfStyle
    
    styleCard = models.StyleCard(**styleCard)
    styleCard.save()

    previousVariants = models.StyleVariant.objects.filter(Style=styleCard).values('id','VariantCode')
    if previousVariants:
        dfPreviousVariants = pd.DataFrame(previousVariants)
    else:
        dfPreviousVariants = pd.DataFrame(columns=['id','VariantCode'])
    del previousVariants

    previousConsumption = models.StyleConsumption.objects.filter(Style=styleCard).values('id','InventoryCode','SizeDetails')
    if previousConsumption:
        dfPreviousConsumption = pd.DataFrame(previousConsumption)
    else:
        dfPreviousConsumption = pd.DataFrame(columns=['id','InventoryCode','SizeDetails'])
    del previousConsumption

    previoiusRoute = models.StyleRoute.objects.filter(Style=styleCard).values('id','Stage')
    if previoiusRoute:
        dfPreviousRoute = pd.DataFrame(previoiusRoute)
    else:
        dfPreviousRoute = pd.DataFrame(columns=['id','Stage'])
    del previoiusRoute
    
    dfVariants.rename(inplace=True, columns={'Variant':'VariantCode'})
    dfVariants = pd.merge(left=dfVariants, right=dfPreviousVariants, left_on='VariantCode', right_on='VariantCode', how='left')

    dfVariants['Style'] = styleCard
    try:
        updateModelWithDF(models.StyleVariant, dfVariants, dfPreviousVariants)
    except Exception as e:
        raise ValueError(f'Error Saving Variants: {e}')
    del dfVariants, dfPreviousVariants

    dfConsumption = dfConsumption[dfConsumption['InvCode'].str.len() > 0]
    
    dfConsumption.rename(inplace=True, columns={'InvCode':'InventoryCode', 'type': 'Type'})

    dfConsumption = pd.merge(left=dfConsumption, right=dfPreviousConsumption, how='left',
                             on=['InventoryCode','SizeDetails'])
    
    dfConsumption['Style'] = styleCard

    dfConsumption['FinalCons'] = calculateFinalConsumption(dfConsumption[['InventoryCode','Unit','Consumption']])
    
    dfConsumption['InventoryCode'] = convertTexttoObject(models.Inventory, dfConsumption['InventoryCode'], 'Code')

    dfConsumption['Unit'] = convertTexttoObject(models.Unit, dfConsumption['Unit'], 'Name')

    dfConsumption['HasVariant'] = np.where(dfConsumption['HasVariant'] == 'true', True, False)

    try:
        pass
        updateModelWithDF(models.StyleConsumption, dfConsumption, dfPreviousConsumption)
    except Exception as e:
        raise ValueError(f'Error Saving Consumption: {e}')
    del dfConsumption, dfPreviousConsumption

    dfRoute.rename(inplace=True, columns={'type':'Stage'})
    dfRoute = pd.merge(left=dfRoute, right=dfPreviousRoute, left_on='Stage', right_on='Stage', how='left')

    dfRoute = dfRoute[dfRoute['Stage'].str.len()>0]

    dfRoute['Style'] = styleCard
    
    try:
        updateModelWithDF(models.StyleRoute, dfRoute, dfPreviousRoute)
    except Exception as e:
        raise ValueError(f'Error Saving Route: {e}')
    del dfRoute, dfPreviousRoute
 
def ProcessStyleData(styleObject: models.StyleCard):   
    style = {
        'StyleCode': styleObject.StyleCode,
        'StyleName': styleObject.StyleName,
        'Customer': styleObject.Customer.Name,
        'Category': styleObject.Category,
        'Notes': styleObject.Notes
    }

    variants = models.StyleVariant.objects.filter(Style=styleObject).values('VariantCode')
    if not variants:
        variants = {'var': [models.StyleVariant()]}
    
    consumption = models.StyleConsumption.objects.filter(Style=styleObject).values('InventoryCode','Consumption','Unit','Type',
                                                                             'FinalCons','HasVariant','SizeDetails')
    
    if not consumption:
        consumption = {'cons': [models.StyleConsumption()]}

    route = models.StyleRoute.objects.filter(Style=styleObject).values('Sequence','Stage')
    if not route:
        route = {'route': [models.StyleRoute()]}
    
    return style, variants, consumption, route