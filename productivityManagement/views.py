from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpRequest

import json
from datetime import datetime

from .theme import theme
from .services import operations_service
from .services.generic_services import paginate, applySearch, refineJson

@login_required(login_url='/login')
def home (request: HttpRequest):
    context = {
        'theme': theme,
    }
    return render (request, 'productivity/home.html', context)

@login_required(login_url='/login')
def Operations (request: HttpRequest):
    if request.method == 'POST':
        pass
    else:
        pageNumber = int(request.GET.get('pageNumber', 1))
        searchTerm = request.GET.get('searchTerm', '')
        sectionFilter = request.GET.get('sectionFilter', None)
        ratePerSAM = request.GET.get('ratePerSAM', 0)

        if ratePerSAM == '':
            ratePerSAM = 0
        
        if ratePerSAM:
            ratePerSAM = float(ratePerSAM)

        Operations, maxRatePerSAM, minRatePerSAM = operations_service.GetOperations(sectionFilter, ratePerSAM)
        Operations = applySearch(Operations, searchTerm)
        page = paginate(Operations, pageNumber)
        context = {
            'operations': page.object_list, 'pageObj': page,
            'maxRatePerSAM': maxRatePerSAM, 'minRatePerSAM': minRatePerSAM, 'ratePerSAM': ratePerSAM,
            'theme': theme
        }
        return render(request, 'Operations/home.html', context)

@login_required(login_url='/login')
def StitchingOBs (request: HttpRequest):
    context = {
        'theme': theme
    }
    return render(request, 'stitchOB/home.html', context)

@login_required(login_url='/login')
def FinishingOBs (request: HttpRequest):
    context = {
        'theme': theme
    }
    return render(request, 'finishOB/home.html', context)

@login_required(login_url='/login')
def ThreadConsumptions (request: HttpRequest):
    context = {
        'theme': theme
    }
    return render(request, 'threadCons/home.html', context)

@login_required(login_url='/login')
def WashingRecipies (request: HttpRequest):
    context = {
        'theme': theme
    }
    return render(request, 'washRecipe/home.html', context)