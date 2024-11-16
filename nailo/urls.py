from django.contrib import admin
from django.urls import path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from nailo_be.views import *

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
    permission_classes=[permissions.AllowAny],
    patterns=urlpatterns,
)

urlpatterns = [
    path("admin/", admin.site.urls), # 관리자 페이지
    path('api/shops/', ShopListView.as_view(), name='shop-list'), # 네일샵 목록 반환
    path('api/home/', HomePageView.as_view(), name='home'),  # 홈 페이지
    path('api/like-list/', LikeListView.as_view(), name='like_list'),  # 좋아요 리스트
    path('api/like-toggle/<uuid:design_key>/', LikeToggleView.as_view(), name='like_toggle'),  # 좋아요 토글
    path('api/nail-design/<uuid:design_key>/', DesignDetailView.as_view(), name='nail_design_detail'), #네일 디자인 상세 페이지
    
    # Swagger documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
