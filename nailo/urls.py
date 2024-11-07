from django.contrib import admin
from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from nailo_BE import views

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
    path('api/nearby-shops/', views.get_nearby_shops, name='get_nearby_shops'), 
    path('api/request-service/', views.request_service, name='request_service'),
    path('api/respond-request/', views.respond_request, name='respond_request'),
    path('api/get-responses/<str:customer_key>/<str:design_key>/', views.get_responses, name='get_responses'),
    
    # Swagger documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


    