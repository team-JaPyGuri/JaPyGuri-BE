from rest_framework import viewsets, status
from rest_framework.response import Response as DRFResponse
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import *
from .models import Shops

class HomePageView(APIView):
    @swagger_auto_schema(
        operation_description="스냅에 들어갈 9개의 네일 디자인을 반환합니다.",
        responses={200: DesignSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        designs = Designs.objects.all()
        random_designs = sample(list(designs), min(len(designs), 9))
        serializer = DesignSerializer(random_designs, many=True)
        return DRFResponse(serializer.data)
    
class LikeListView(APIView):
    def get(self, request, *args, **kwargs):
        # 현재 사용자 기반 좋아요 리스트
        user = request.user
        liked_designs = Like.objects.filter(user=user)
        serializer = DesignSerializer([like.design for like in liked_designs], many=True)
        return DRFResponse(serializer.data)

class NailDesignDetailView(APIView):
    def get(self, request, design_id, *args, **kwargs):
        try:
            design = Design.objects.get(id=design_id)
            serializer = DesignSerializer(design)
            return DRFResponse(serializer.data)
        except Design.DoesNotExist:
            raise NotFound({"error": "Design not found"})
        
class ShopListView(APIView):
    def get(self, request, *args, **kwargs):
        shops = Shops.objects.all()
        serializer = ShopSerializer(shops, many=True) 
        return DRFResponse(serializer.data)