from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required

from .theme import theme

@login_required(login_url='/login')
def Home (request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)

    context = {'theme': theme}
    return render(request, 'prodManagement/home.html', context)

@login_required(login_url='/login')
def Operations (request:HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not Allowed', status=401)
    
    context = {
        'theme': theme,
    }
    return render(request, 'operations/home.html', context)