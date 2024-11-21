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
                return Response({'message': 'Customer data', 'data': {
                    'customer_id': user.customer_id,
                    'customer_name': user.customer_name,
                }})
            elif user_type == 'shop':
                return Response({'message': 'Shop data', 'data': {
                    'shop_id': user.shop_id,
                    'shop_name': user.shop_name,
                }})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        
class HomePagePagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'page_size'
    max_page_size = 100


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
    
class NailTryOnView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_description="Upload a hand image and apply a nail design using an AI model.",
        
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'image': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description="Hand image to be processed"
                ),
            },
            required=['image'],
        ),
        responses={
            200: openapi.Response(
                description="Successfully applied nail design",
                examples={
                    "application/json": {
                        "message": "네일 디자인이 적용된 이미지를 생성했습니다.",
                        "image_url": "/media/generated_images/123_generated.jpg"
                    }
                }
            ),
            400: openapi.Response(description="Bad request or missing fields"),
            500: openapi.Response(description="Server error"),
        }
    )
    
    def post(self, request, *args, **kwargs):
        user_type_header = request.headers.get("X-User-Type")
        user_id = request.headers.get("X-User-Id")

        if not user_type_header or not user_id:
            return DRFResponse({"error": "사용자 정보를 헤더에 포함해야 합니다."}, status=400)

        user, user_type = get_user_id(user_type_header, user_id)
        if not user or user_type != "customer":
            return DRFResponse({"error": "유효하지 않은 사용자입니다."}, status=403)
            
        image = request.FILES.get('image')
        if not image:
            return Response({"error": "이미지가 필요합니다."}, status=400)
        
        model_url = "" # 추후 변경 필요 !!!
        
        # 모델 서버에 요청
        try:
            files = {'image': image_file}  # 이미지 파일 포함
            response = requests.post(model_url, files=files)

            if response.status_code != 200:
                return Response({"error": "AI 모델 서버에서 오류가 발생했습니다."}, status=500)

            # 처리된 이미지 데이터 수신
            response_data = response.json()
            processed_image_data = response_data.get('image')

            if not processed_image_data:
                return Response({"error": "AI 모델 서버로부터 이미지를 받을 수 없습니다."}, status=500)

        except Exception as e:
            return Response({"error": f"AI 모델 서버와 통신 중 오류 발생: {str(e)}"}, status=500)
        
        try:
            processed_image = apply_nail_design(uploaded_image)
        except Exception as e:
            return Response({"error": f"AI 모델 호출 중 오류 발생: {str(e)}"}, status=500)

         # 처리된 이미지 저장
        try:
            output_image = f"generated_images/{user_id}_generated.jpg"
            output_path = os.path.join(settings.MEDIA_ROOT, output_image)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)  # 디렉토리 생성

            # 수신된 이미지 데이터를 저장
            image_data = BytesIO()
            image_data.write(processed_image_data.encode('latin1'))  # 모델 서버에서 받은 데이터를 디코딩
            image_data.seek(0)

            with open(output_path, 'wb') as f:
                f.write(image_data.read())

            # URL 저장
            customer.generated_image = default_storage.url(output_image)
            customer.save()

        except Exception as e:
            return Response({"error": f"이미지를 저장하는 중 오류 발생: {str(e)}"}, status=500)

        return Response({
            "message": "입혀보기 이미지를 생성했습니다.",
            "image_url": customer.generated_image
        }, status=200)