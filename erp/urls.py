from django.contrib import admin
from django.urls import path, include
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

def home(request: HttpRequest):
    if request.method != 'GET':
        return HttpResponse('Not allowed', status=403)
    
    return render(request, 'erp_home.html')

urlpatterns = [
    path('', home),
    path('home', home, name='home'),
    path('admin/', admin.site.urls),
    path ('', include ('django.contrib.auth.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path ('', include ('apparelManagement.urls')),
    path ('', include ('qualityControl.urls')),
    path ('', include ('marketing.urls')),
    path ('', include ('prodManagement.urls')),
]