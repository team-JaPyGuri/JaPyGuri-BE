from rest_framework import viewsets, status
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import *
from .models import *
from .utils import get_user_id

import random

class UserDetailView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            # 헤더에서 사용자 타입과 ID 가져오기
            user_type = request.headers.get('X-User-Type')
            user_id = request.headers.get('X-User-Id')

            # 사용자 객체 가져오기
            user, user_type = get_user_by_type_and_id(user_type, user_id)

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
        
class HomePageView(APIView):
    @swagger_auto_schema(
        operation_description="스냅에 들어갈 9개의 네일 디자인을 반환합니다.",
        responses={200: DesignSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        designs = Designs.objects.all()
        random_designs = random.sample(list(designs), min(len(designs), 9))
        serializer = DesignSerializer(random_designs, many=True)
        return DRFResponse(serializer.data)
    
class LikeListView(APIView):
    def get(self, request, *args, **kwargs):
        # 현재 사용자 기반 좋아요 리스트
        user_type = request.headers.get('X-User-Type')
        user_id = request.headers.get('X-User-Id')
        if not user_type or not user_id:
            return DRFResponse({"error": "사용자 정보를 헤더에 포함해야 합니다."}, status=400)
        
        customer = get_user_id(user_type, user_id)

        if customer is None:
            return DRFResponse({"error": "유효하지 않은 사용자입니다."}, status=403)

        liked_designs = Like.objects.filter(customer=customer)
        if not liked_designs.exists():  # 좋아요 내역이 없는 경우
            return DRFResponse({"message": "좋아요 내역이 없습니다."}, status=200)
        
        designs = [like.design for like in liked_designs]
        serializer = DesignSerializer(designs, many=True)
        return DRFResponse(serializer.data, status=200)

class LikeToggleView(APIView):
    def post(self, request, design_key, *args, **kwargs):
        """좋아요 토글 기능"""
        user_type = request.headers.get('X-User-Type')
        user_id = request.headers.get('X-User-Id')
        if not user_type or not user_id:
            return DRFResponse({"error": "사용자 정보를 헤더에 포함해야 합니다."}, status=400)

        customer = get_user_id(user_type, user_id)
        if customer is None:
            return DRFResponse({"error": "유효하지 않은 사용자입니다."}, status=404)

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
    def get(self, request, design_key, *args, **kwargs):
        try:
            design = Designs.objects.get(design_key=design_key)
            serializer = DesignSerializer(design)
            return DRFResponse(serializer.data)
        except Designs.DoesNotExist:
            raise NotFound({"error": "Design not found"})
        
class ShopListView(APIView):
    def get(self, request, *args, **kwargs):
        shops = Shops.objects.all()
        serializer = ShopSerializer(shops, many=True) 
        return DRFResponse(serializer.data)