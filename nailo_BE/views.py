from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from geopy.distance import distance
from .serializers import *
import json

class NailServiceViewSet(viewsets.ViewSet):
    
    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter('lat', openapi.IN_QUERY, description="User's latitude", type=openapi.TYPE_NUMBER),
            openapi.Parameter('lng', openapi.IN_QUERY, description="User's longitude", type=openapi.TYPE_NUMBER),
        ],
        responses={200: ShopSerializer(many=True)}
    )
    @action(detail=False, methods=['GET'], url_path='nearby-shops', name='nearby_shops')
    def nearby_shops(self, request):
        """
        유저 현재 위치 중심으로 주변 샵 거리 정렬 후 반환
        """
        user_lat = request.GET.get('lat')
        user_lng = request.GET.get('lng')
        
        if user_lat is None or user_lng is None:
            return DRFResponse(
                {"error": "Latitude and longitude are required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shops = Shops.objects.all()
        sorted_shops = sorted(
            shops,
            key=lambda shop: distance((float(user_lat), float(user_lng)), (shop.lat, shop.lng)).km
        )
        
        serializer = ShopSerializer(sorted_shops[:5], many=True)
        return DRFResponse(serializer.data)

    @swagger_auto_schema(
        method='post',
        request_body=RequestSerializer,
        responses={200: AddRequestSerializer(many=True)}
    )
    
    @action(detail=False, methods=['POST'], url_path='respond-service', name='respond_service')
    def request_service(self, request):
        """
        주변 샵에 시술 요청
        """
        serializer = RequestSerializer(data=request.data)
        print("도착정보: ", serializer)
        if not serializer.is_valid():
            print("Request Service Validation Errors:", serializer.errors)
            return DRFResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        design_id = data['design_key']
        customer_id = data['customer_key']
        
        try:
            design = Designs.objects.get(design_key=design_id)
            price = design.price
            
            if request.META.get('HTTP_TEST_MODE'):
                nearby_shops = [
                    {"shopper_key": str(shop.shopper_key)}
                    for shop in Shops.objects.all()[:1]
                ]
            else:
                nearby_shops_response = self.nearby_shops(request)
                if nearby_shops_response.status_code != 200:
                    return nearby_shops_response
                nearby_shops = nearby_shops_response.data
            
            responses = []
            for shop_data in nearby_shops:
                shop = Shops.objects.get(shopper_key=shop_data['shopper_key'])
                customer = Customers.objects.get(customer_key=customer_id)
                
                existing_request = Request.objects.filter(
                    customer=customer, shop=shop, design=design
                )
                
                if not existing_request.exists():
                    request_instance = Request.objects.create(
                        customer=customer,
                        shop=shop,
                        design=design,
                        price=price,
                        status="pending",
                        contents=data.get('contents', '')
                    )
                    
                    responses.append(request_instance)
                
            serializer = AddRequestSerializer(responses, many=True)
            return DRFResponse({"status": "success", "requests": serializer.data})
            
        except (Designs.DoesNotExist, Customers.DoesNotExist, Shops.DoesNotExist) as e:
            return DRFResponse({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        method='post',
        request_body=ResponseSerializer,
        responses={200: openapi.Response('Response submitted successfully')}
    )
    @action(detail=False, methods=['POST'], url_path='respond-service', name='respond_service')
    def respond_service(self, request):
        """
        요청에 따라 accept/reject로 상태 변경 후 응답
        """
        serializer = ResponseListSerializer(data=request.data)
        if not serializer.is_valid():
            print("Request Service Validation Errors:", serializer.errors)
            return DRFResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        request_key = data['request_key']
        shop_response = data['response']
        price = data.get('price')
        contents = data.get('contents', '')

        try:
            request_instance = Request.objects.get(request_key=request_key)
            
            if shop_response == 'accepted':
                price = request_instance.price if price is None else price
                request_instance.status = 'accepted'
                
                if not Response.objects.filter(request=request_instance).exists():
                    Response.objects.create(
                        customer=request_instance.customer,
                        shop=request_instance.shop,
                        request=request_instance,
                        price=price,
                        contents=contents
                    )
            else:
                request_instance.status = 'rejected'
            
            request_instance.save()
            return DRFResponse({
                "message": "Response submitted successfully", 
                "status": request_instance.status
            })

        except Request.DoesNotExist:
            return DRFResponse({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter('customer_key', openapi.IN_PATH, type=openapi.TYPE_STRING),
            openapi.Parameter('design_key', openapi.IN_PATH, type=openapi.TYPE_STRING),
        ],
        responses={200: ResponseListSerializer(many=True)}
    )
    @action(detail=False, methods=['GET'], url_path='responses/(?P<customer_key>[^/.]+)/(?P<design_key>[^/.]+)')
    def get_responses(self, request, customer_key, design_key):
        """
        요청 응답(a.k.a 채팅방) 불러오기
        """
        try:
            responses = Response.objects.filter(
                customer__customer_key=customer_key,
                request__design__design_key=design_key
            )
            
            serializer = ResponseListSerializer(responses, many=True)
            return DRFResponse(serializer.data)
            
        except Exception as e:
            return DRFResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)