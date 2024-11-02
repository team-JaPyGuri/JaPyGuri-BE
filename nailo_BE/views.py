from django.shortcuts import render
from django.http import JsonResponse
from .models import NailShop
import geopy.distance

def get_nearby_shops(request):
    # 요청에서 사용자 위치 좌표 받기
    user_lat = float(request.GET.get('lat'))
    user_lng = float(request.GET.get('lng'))

    # 데이터베이스의 네일샵 목록을 가져와 사용자 위치와의 거리 계산
    shops = NailShop.objects.all()
    sorted_shops = sorted(
        shops,
        key=lambda shop: geopy.distance.distance(
            (user_lat, user_lng),
            (shop.latitude, shop.longitude)
        ).km
    )

    # 상위 5개의 가까운 네일샵 정보를 JSON 형태로 응답
    response_data = [{
        "name": shop.name,
        "latitude": shop.latitude,
        "longitude": shop.longitude,
        "address": shop.address
    } for shop in sorted_shops[:5]]

    return JsonResponse(response_data, safe=False)
