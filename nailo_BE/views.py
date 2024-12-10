import os
from django.conf import settings

from pathlib import Path
from django.http import JsonResponse

from channels.layers import get_channel_layer 
from asgiref.sync import async_to_sync

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

from PIL import Image
import base64
import shutil  
import requests
import random
import re 
import logging

logger = logging.getLogger(__name__)

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
        query_type = request.query_params.get('type', 'random')  # 기본값은 'random'
        designs = Designs.objects.all().order_by('-created_at')

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
            design.like_count = design.like_count = design.like_count - 1
            design.save()
            return DRFResponse({"message": "좋아요가 취소되었습니다.", "like_count": design.like_count}, status=status.HTTP_200_OK)

        # 좋아요 추가
        design.like_count = design.like_count + 1
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

class DesignListView(APIView):
    """네일샵 리스트 반환 기능"""
    @swagger_auto_schema(
        operation_description="모든 네일 디자인 목록을 반환합니다.",
        responses={200: DesignSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        designs = Designs.objects.all()
        serializer = DesignSerializer(designs, many=True) 
        return DRFResponse(serializer.data)

def manage_directory_files(directory_path, max_files=10):
    """
    디렉토리 내 파일 수를 관리하고 데이터베이스를 동기화하는 함수
    가장 오래된 파일부터 삭제하여 최대 파일 수를 유지
    """
    try:
        files = list(Path(directory_path).glob('*'))
        files.sort(key=lambda x: x.stat().st_ctime)
        
        while len(files) >= max_files:
            oldest_file = files.pop(0) 
            try:
                filename = oldest_file.name
                
                # DB에 저장된 형식과 동일한 경로로 구성
                if "predicted" in str(oldest_file):
                    db_path = f"/tryon/predicted/{filename}"
                    TryOnHistory.objects.filter(predicted_image=db_path).delete()
                else:
                    db_path = f"/tryon/hand/{filename}"
                    TryOnHistory.objects.filter(original_image=db_path).delete()
                
                if oldest_file.exists():
                    oldest_file.unlink()
                    logger.info(f"Deleted file {oldest_file} and its database record with path {db_path}")
                
            except Exception as e:
                logger.error(f"Error in file deletion process for {oldest_file}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error managing directory {directory_path}: {str(e)}")
        
class TryOnView(APIView):
    parser_classes = [MultiPartParser]

    @swagger_auto_schema(
        operation_summary="네일 입혀보기 기능",
        operation_description="""
        사용자가 손 사진을 업로드하고 네일 디자인 키를 제공하면 FastAPI 모델 서버를 통해 처리된 결과를 반환합니다.
        처리 결과는 WebSocket을 통해 사용자에게 전송됩니다.
        """,
        manual_parameters=[
            openapi.Parameter(
                name="x-user-type",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description="사용자 유형 (customer 또는 shop)"
            ),
            openapi.Parameter(
                name="x-user-id",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                required=True,
                description="사용자 ID"
            ),
            openapi.Parameter(
                name="design_key",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                required=True,
                description="design key(필수)"
            ),
            openapi.Parameter(
                name="image",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description="업로드할 손 사진 파일 (png, jpg, jpeg 형식만 지원)"
            ),
        ],
        responses={
            200: openapi.Response(
                description="이미지 업로드 및 처리 성공",
                examples={
                    "application/json": {
                        "message": "이미지가 생성되었습니다.",
                        "original_image": "/media/tryon/hand/0ad0f443-1464-4104-9755-f252f10825ba.png",
                        "predicted_image": "/media/tryon/predicted/predicted_0ad0f443-1464-4104-9755-f252f10825ba.png",
                        "design_key" : "uuid",
                    }
                }
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={
                    "application/json": {
                        "error": "Design key is required."
                    }
                }
            ),
            404: openapi.Response(
                description="디자인을 찾을 수 없음",
                examples={
                    "application/json": {
                        "error": "Design not found."
                    }
                }
            ),
            500: openapi.Response(
                description="서버 에러",
                examples={
                    "application/json": {
                        "error": "Model server communication error: ..."
                    }
                }
            ),
        },
    )

    def post(self, request):
        user_type = request.headers.get("X-User-Type")
        user_id = request.headers.get("X-User-Id")
        if not user_type or not user_id:
            return JsonResponse({"error": "User headers are missing."}, status=400)

        if "image" not in request.FILES:
            return JsonResponse({"error": "No hand image file provided."}, status=400)

        hand_image = request.FILES["image"]
        if not hand_image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            return JsonResponse({"error": "Invalid hand image format."}, status=400)

        design_key = request.data.get("design_key")
        if not design_key:
            return JsonResponse({"error": "Design key is required."}, status=400)

        try:
            design = Designs.objects.get(design_key=design_key)
            design_name = design.design_name

            # design_name에서 숫자 ID 추출
            match = re.search(r'Design (\d+)', design_name, re.IGNORECASE)
            if not match:
                return JsonResponse({"error": "Invalid design name format."}, status=400)
            original_id = match.group(1)
            
            # ID 매핑 테이블
            design_mapping = {
                "1": 1,
                "10": 2,
                "11": 3,
                "12": 4,
                "13": 5,
                "14": 6,
                "15": 7,
                "16": 8,
                "17": 9,
                "18": 10,
            }

            mapped_id = design_mapping.get(original_id)
            if not mapped_id:
                return JsonResponse({"error": f"Invalid design ID: {original_id}"}, status=400)
            
            unique_filename = f"{uuid.uuid4()}.png"
            hand_image_path = Path(settings.MEDIA_ROOT) / "tryon/hand" / unique_filename
            predicted_path_dir = Path(settings.MEDIA_ROOT) / "tryon/predicted"
            
            os.makedirs(hand_image_path.parent, exist_ok=True)
            os.makedirs(predicted_path_dir, exist_ok=True)

            manage_directory_files(hand_image_path.parent)
            manage_directory_files(predicted_path_dir)

            with open(hand_image_path, "wb") as f:
                for chunk in hand_image.chunks():
                    f.write(chunk)
                    
            # 모델 서버 url
            model_server_url = "https://52b9-211-117-82-98.ngrok-free.app/predict"
            
            files = {
                "image": (hand_image.name, open(hand_image_path, "rb"), "image/png"),
            }
            data = {"design_name": mapped_id}
            
            response = requests.post(model_server_url, files=files, data=data)
            if response.status_code != 200:
                return JsonResponse({"error": f"Model server error: {response.text}"}, status=500)

            predicted_filename = f"predicted_{unique_filename}"
            predicted_path = Path(settings.MEDIA_ROOT) / "tryon/predicted" / predicted_filename
            os.makedirs(predicted_path.parent, exist_ok=True)

            temp_path = predicted_path.parent / f"temp_{predicted_filename}"

            try:
                # base64 디코딩 후 임시 저장
                image_data = base64.b64decode(response.json()['image_data'])
                with open(temp_path, "wb") as temp_file:
                    temp_file.write(image_data)
                
                # 이미지 유효성 검사
                try:
                    with Image.open(temp_path) as img:
                        img.verify()
                    print(f"이미지가 정상적으로 수신되었습니다. 크기: {os.path.getsize(temp_path)} bytes")
                    
                    # 정상이면 실제 위치로 이동
                    shutil.move(temp_path, predicted_path)
                except Exception as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise ValueError(f"수신된 이미지가 손상되었습니다: {str(e)}")
            except Exception as e:
                return JsonResponse({"error": f"이미지 처리 중 오류 발생: {str(e)}"}, status=500)

            # WebSocket 및 히스토리 저장
            try:
                customer = Customers.objects.get(customer_id=user_id)
                design = Designs.objects.get(design_key=design_key)
                
                TryOnHistory.objects.create(
                    user=customer,
                    original_image=f"/tryon/hand/{unique_filename}",
                    predicted_image=f"/tryon/predicted/{predicted_filename}",
                    design_key=design,
                )

                group_name = f"customer_{customer.customer_key}"
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "notify_tryon_result",
                        "original_image": f"/media/tryon/hand/{unique_filename}",
                        "predicted_image": f"/media/tryon/predicted/{predicted_filename}",
                        "design_key": str(design_key)
                    },
                )
            except Exception as e:
                logger.error(f"WebSocket message error: {str(e)}")

            return JsonResponse({
                "message": "이미지가 생성되었습니다.",
                "original_image": f"/media/tryon/hand/{unique_filename}",
                "predicted_image": f"/media/tryon/predicted/{predicted_filename}",
                "design_key": design_key,
            }, status=200)
        except Designs.DoesNotExist:
            return JsonResponse({"error": "Design not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
class TryOnHistoryView(APIView):
    @swagger_auto_schema(
        operation_summary="Try On History",
        operation_description="사용자의 네일 입혀보기 기록을 반환합니다.",
        responses={
            200: openapi.Response(
                description="히스토리 반환",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "original_image": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="원본 이미지 URL"
                            ),
                            "predicted_image": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="처리된 이미지 URL"
                            ),
                            "created_at": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format="date-time",
                                description="생성 날짜"
                            ),
                            "design_key": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="디자인 키"
                            ),
                        }
                    )
                ),
                examples={
                    "application/json": [
                        {
                            "original_image": "http://localhost:8001/media/tryon/hand/15257_35734_0936.jpg",
                            "predicted_image": "http://localhost:8001/media/tryon/predicted/predicted_15257_35734_0936.jpg",
                            "created_at": "2024-11-25T06:03:26.350928Z",
                            "design_key": "012869af-6557-4cab-b1a8-019445c1fed1"
                        }
                    ]
                },
            ),
            400: openapi.Response(description="잘못된 요청"),
            404: openapi.Response(description="사용자 없음"),
        },
    )
    def get(self, request):
        user_type = request.headers.get("X-User-Type")
        user_id = request.headers.get("X-User-Id")

        if not user_type or not user_id or user_type != "customer":
            return DRFResponse({"error": "Invalid user headers"}, status=400)

        try:
            customer = Customers.objects.get(customer_id=user_id)
        except Customers.DoesNotExist:
            return DRFResponse({"error": "User not found"}, status=404)

        history = TryOnHistory.objects.filter(user=customer).order_by('-created_at')
        data = []
        for item in history:
            try:
                original_image_url = (
                    request.build_absolute_uri(item.original_image.url).replace('http://', 'https://')
                    if item.original_image else None
                )
                predicted_image_url = (
                    request.build_absolute_uri(item.predicted_image.url).replace('http://', 'https://')
                    if item.predicted_image else None
                )
                # 배포 서버
                # original_image_url = (
                #     request.build_absolute_uri(item.original_image.url).replace('http://', 'https://')
                #     if item.original_image else None
                # )
                # predicted_image_url = (
                #     request.build_absolute_uri(item.predicted_image.url).replace('http://', 'https://')
                #     if item.predicted_image else None
                # )
                data.append({
                    "original_image": original_image_url,
                    "predicted_image": predicted_image_url,
                    "created_at": item.created_at,
                    "design_key": item.design_key.design_key,
                })
            except Exception as e:
                data.append({
                    "original_image": None,
                    "predicted_image": None,
                    "created_at": item.created_at,
                    "design_key": item.design_key.design_key,
                    "error": str(e)
                })
        return DRFResponse(data, status=200)