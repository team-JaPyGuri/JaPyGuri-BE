from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from nailo_BE.views import *

# DRF Router 설정
router = DefaultRouter()
router.register(r'api/nail-service', NailServiceViewSet, basename='nail-service')

# Swagger 설정
schema_view = get_schema_view(
    openapi.Info(
        title="Nailo API",
        default_version='v1',
        description="Nailo BE API 문서",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="12211598a@inha.ac.kr"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # ViewSet URLs
    path('', include(router.urls)),
    path('api/shops/', ShopListView.as_view(), name='shop-list'),
    
    # Swagger documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]