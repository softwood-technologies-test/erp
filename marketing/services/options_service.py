import pandas as pd

from django_countries import countries
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from .. import models

@login_required(login_url='/login')
def GetCountries(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=405)
    
    listOfCountries = []
    for code, name in list(countries):
        listOfCountries.append({'CountryCode': code, 'CountryName': name})
    
    dfCountries = pd.DataFrame(listOfCountries)
    del listOfCountries
    
    countriesCount = models.Customer.objects.values('Country').annotate(Count=Count('Country'))
    dfCountriesCount = pd.DataFrame(countriesCount)

    dfCountries = pd.merge(left=dfCountries, right=dfCountriesCount, left_on='CountryCode', right_on='Country', how='left')

    dfCountries = dfCountries.sort_values(by='Count', ascending=False)
    dfCountries.drop(inplace=True, columns=['Country', 'Count'])

    dfCountries.rename(inplace=True, columns={'CountryCode':'value', 'CountryName': 'text'})

    cols = [i for i in dfCountries]
    data = [dict(zip(cols, i)) for i in dfCountries.values]

    return JsonResponse(data, safe=False)