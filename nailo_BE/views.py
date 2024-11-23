from rest_framework import viewsets, status
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import *
from .models import *
from .utils import get_user_id

import random

class UserDetailView(APIView):
    @swagger_auto_schema(
        operation_description="사용자 타입과 ID를 기반으로 사용자 정보를 반환합니다.",
        
        manual_parameters=[
            openapi.Parameter(
                'X-User-Type',
                openapi.IN_HEADER,
                description="유저 타입 ('customer' or 'shop')",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'X-User-Id',
                openapi.IN_HEADER,
                description="Unique identifier for the user",
                type=openapi.TYPE_STRING,
                required=True
            ),
        ],
        
        responses={
            200: openapi.Response(
                "사용자 정보 반환",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                    },
                ),
            ),
            400: "Bad Request",
        },
    )
    def get(self, request, *args, **kwargs):
        try:
            user_type_header = request.headers.get("X-User-Type")
            user_id = request.headers.get("X-User-Id")

            if not user_type_header or not user_id:
                return DRFResponse({"error": "사용자 정보를 헤더에 포함해야 합니다."}, status=400)

            user, user_type = get_user_id(user_type_header, user_id)
            # 만약 packing 관련 오류라면 둘 중 하나가 invalid
            if not user or user_type != "customer":
                return DRFResponse({"error": "유효하지 않은 사용자입니다."}, status=403)

            if user_type == 'customer':
                return DRFResponse({'message': 'Customer data', 'data': {
                    'customer_id': user.customer_id,
                    'customer_name': user.customer_name,
                }})
            elif user_type == 'shop':
                return DRFResponse({'message': 'Shop data', 'data': {
                    'shop_id': user.shop_id,
                    'shop_name': user.shop_name,
                }})
        except ValueError as e:
            return DRFResponse({'error': str(e)}, status=400)
        
class HomePagePagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return DRFResponse({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })
        
class HomePageView(APIView):
    @swagger_auto_schema(
        operation_description="홈 화면: 랜덤 디자인 반환 또는 전체 디자인의 페이지네이션 반환",
        manual_parameters=[
            openapi.Parameter(
                'type',
                openapi.IN_QUERY,
                description="'random' (9개) 또는 'all' (스냅 페이지네이션)",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="페이지 번호 (type=all일 때 필요)",
                type=openapi.TYPE_INTEGER,
                required=False,
            ),
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "results": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                    "count": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "next": openapi.Schema(type=openapi.TYPE_STRING),
                    "previous": openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
            400: "Invalid 'type' parameter",
        },
    )
    def get(self, request, *args, **kwargs):
        # 쿼리 파라미터 확인
        query_type = request.query_params.get('type', 'random')  # 기본값은 'random'
        designs = Designs.objects.filter(is_active=True).order_by('-created_at')

        if query_type == 'random':
            return self._get_random_designs(designs)

        elif query_type == 'all':
            return self._get_paginated_designs(designs, request)

        return DRFResponse({"error": "Invalid 'type' parameter. Use 'random' or 'all'."}, status=400)

    def _get_random_designs(self, designs):
        """HotNailList-랜덤 9개 디자인 반환"""
        random_designs = random.sample(list(designs), min(len(designs), 9))
        serializer = DesignSerializer(random_designs, many=True)
        return DRFResponse(serializer.data)

    def _get_paginated_designs(self, designs, request):
        """스냅-전체 디자인 반환 (페이지네이션)"""
        paginator = HomePagePagination()
        paginated_designs = paginator.paginate_queryset(designs, request, view=self)
        serializer = DesignSerializer(paginated_designs, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class LikeListView(APIView):
    @swagger_auto_schema(
        operation_description="현재 사용자 기반 좋아요 리스트를 반환합니다.",
        responses={
            200: DesignSerializer(many=True),
            400: "사용자 정보를 헤더에 포함해야 합니다.",
            403: "유효하지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        # 현재 사용자 기반 좋아요 리스트
        user_type_header = request.headers.get("X-User-Type")
        user_id = request.headers.get("X-User-Id")

        if not user_type_header or not user_id:
            return DRFResponse({"error": "사용자 정보를 헤더에 포함해야 합니다."}, status=400)

        user, user_type = get_user_id(user_type_header, user_id)
        if not user or user_type != "customer":
            return DRFResponse({"error": "유효하지 않은 사용자입니다."}, status=403)

        customer = user
        
        liked_designs = Like.objects.filter(customer=customer)
        if not liked_designs.exists():
            return DRFResponse({"message": "좋아요 내역이 없습니다."}, status=200)

        designs = [like.design for like in liked_designs]
        serializer = DesignSerializer(designs, many=True)
        return DRFResponse(serializer.data, status=200)

class LikeToggleView(APIView):
    @swagger_auto_schema(
        operation_description="좋아요 토글 기능 (좋아요 추가/취소)",
        responses={
            201: openapi.Response(
                "좋아요가 추가되었습니다.",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "like_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            200: openapi.Response(
                "좋아요가 취소되었습니다.",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "like_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            404: "Design not found",
        },
    )
    def post(self, request, design_key, *args, **kwargs):
        """좋아요 토글 기능"""
        user_type_header = request.headers.get("X-User-Type")
        user_id = request.headers.get("X-User-Id")

        if not user_type_header or not user_id:
            return DRFResponse({"error": "사용자 정보를 헤더에 포함해야 합니다."}, status=400)

        user, user_type = get_user_id(user_type_header, user_id)
        if not user or user_type != "customer":
            return DRFResponse({"error": "유효하지 않은 사용자입니다."}, status=403)

        customer = user
        
        try:
            design = Designs.objects.get(pk=design_key)
        except Designs.DoesNotExist:
            return DRFResponse({"error": "Design not found"}, status=status.HTTP_404_NOT_FOUND)

        like, created = Like.objects.get_or_create(customer=customer, design=design)

        if not created:
            # 좋아요 취소
            like.delete()
            design.like_count = Like.objects.filter(design=design).count()
            design.save()
            return DRFResponse({"message": "좋아요가 취소되었습니다.", "like_count": design.like_count}, status=status.HTTP_200_OK)

        # 좋아요 추가
        design.like_count = Like.objects.filter(design=design).count()
        design.save()
        return DRFResponse({"message": "좋아요가 추가되었습니다.", "like_count": design.like_count}, status=status.HTTP_201_CREATED)

class DesignDetailView(APIView):
    @swagger_auto_schema(
        operation_description="디자인 상세 정보를 반환합니다.",
        responses={
            200: DesignSerializer,
            404: "Design not found",
        },
    )
    def get(self, request, design_key, *args, **kwargs):
        try:
            design = Designs.objects.get(design_key=design_key)
            serializer = DesignSerializer(design)
            return DRFResponse(serializer.data)
        except Designs.DoesNotExist:
            raise NotFound({"error": "Design not found"})
        
class ShopListView(APIView):
    """네일샵 리스트 반환 기능"""
    @swagger_auto_schema(
        operation_description="모든 네일샵 목록을 반환합니다.",
        responses={200: ShopSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        shops = Shops.objects.all()
        serializer = ShopSerializer(shops, many=True) 
        return DRFResponse(serializer.data)