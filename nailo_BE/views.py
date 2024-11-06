import json
from django.shortcuts import render
from django.http import JsonResponse
from geopy.distance import geodesic, distance
import uuid
from .models import *

def get_nearby_shops(request):
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')

    print("Received latitude:", user_lat)
    print("Received longitude:", user_lng)
    
    # 예외처리: 유저 현재 위치가 반환되지 않음
    if user_lat is None or user_lng is None:
        return JsonResponse({"error": "Latitude and longitude are required."}, status=400)
    
    shops = Shops.objects.all()
    sorted_shops = sorted(
        shops,
        key=lambda shop: distance((user_lat, user_lng), (shop.lat, shop.lng)).km
    )
    
    response_data = [{
        "shopper_key": shop.shopper_key,
        "name": shop.shopper_name,
        "latitude": shop.lat,
        "longitude": shop.lng
    } for shop in sorted_shops[:5]]
    
    return JsonResponse(response_data, safe=False)

def request_service(request):
    data = json.loads(request.body)  
    design_id = data.get('design_key')
    customer_id = data.get('customer_key')
    
    # 기본값: 디자인 원래 가격
    design = Designs.objects.get(design_key=design_id)
    price = design.price
    
    # 반경 내 네일샵 검색
    nearby_shops = get_nearby_shops(request)
    
    responses = []
    for shop_data in nearby_shops:
        shop = Shops.objects.get(shopper_key=shop_data['shopper_key'])
        request_instance = Request.objects.create(
            customer=Customers.objects.get(customer_key=customer_id),
            shop=shop,
            design=design,
            price=price,
            status="pending",
            contents=data.get('contents', '') # 남길 메모 없으면 빈칸으로
        )
        responses.append({
            "request_key": str(request_instance.request_key),
            "shop_name": shop.shopper_name,
            "status": request_instance.status
        })

    return JsonResponse({"status": "success", "requests": responses})

def respond_request(request):
    data = json.loads(request.body)  
    request_key = uuid.UUID(data.get('request_key'))  
    shop_response = data.get('response')  # 'accepted' or 'rejected' 가능
    price = data.get('price')
    contents = data.get('contents', '')

    try:
        request_instance = Request.objects.get(request_key=request_key)
        
        if shop_response == 'accepted':
            if not price:  # 가격이 없으면 요청의 원래 가격 사용
                price = request_instance.price
            request_instance.status = 'accepted'
            
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
        return JsonResponse({"message": "Response submitted successfully", "status": request_instance.status})

    except Request.DoesNotExist:
        return JsonResponse({"error": "Request not found"}, status=404)
    
def get_responses(request, customer_key, design_key):
    responses = Response.objects.filter(
        customer__customer_key=customer_key,
        request__design__design_key=design_key
    )

    response_data = [{
        "response_key": str(response.response_key),
        "shop_name": response.shop.shopper_name,
        "price": response.price,
        "contents": response.contents,
        "status": response.request.status
    } for response in responses]

    return JsonResponse(response_data, safe=False)