"""
URL configuration for nailo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from nailo_BE import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/nearby-shops/', views.get_nearby_shops, name='get_nearby_shops'), 
    path('api/request-service/', views.request_service, name='request_service'),
    path('api/respond-request/', views.respond_request, name='respond_request'),
    path('api/get-responses/<str:customer_key>/<str:design_key>/', views.get_responses, name='get_responses'),
]