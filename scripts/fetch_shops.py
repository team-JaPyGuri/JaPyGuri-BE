import os
import sys
import django
import requests
from dotenv import load_dotenv
from decimal import Decimal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")  
django.setup()

from nailo_be.models import Shops 

load_dotenv()

client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")
search_url = "https://openapi.naver.com/v1/search/local.json"

# 네이버 Geocoding API 설정
geocode_client_id = os.getenv("NAVER_GEOCODE_CLIENT_ID")
geocode_client_secret = os.getenv("NAVER_GEOCODE_CLIENT_SECRET")
geocode_url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"

# 네이버 검색 API 요청 헤더
headers = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret
}

# 네이버 Geocoding API 요청 헤더
geocode_headers = {
    "X-NCP-APIGW-API-KEY-ID": geocode_client_id,
    "X-NCP-APIGW-API-KEY": geocode_client_secret
}

# 검색 파라미터
params = {
    "query": "인하대 네일",
    "display": 10,
    "start": 1,   
    "sort": "comment" 
}

# API 요청 보내기
response = requests.get(search_url, headers=headers, params=params)

# 요청 성공 여부 확인
if response.status_code == 200:
    data = response.json()
    for item in data['items']:
        shopper_key = item.get('id', '')
        shopper_id = item.get('category', '')
        shopper_name = item['title'].replace("<b>", "").replace("</b>", "")
        intro_image = item.get('link', '')
        address = item['address']

        # Geocoding API를 사용해 주소를 위경도 좌표로 변환
        geocode_params = {"query": address}
        geocode_response = requests.get(geocode_url, headers=geocode_headers, params=geocode_params)

        if geocode_response.status_code == 200:
            geocode_data = geocode_response.json()
            if geocode_data['addresses']:
                lat = Decimal(str(geocode_data['addresses'][0]['y']))
                lng = Decimal(str(geocode_data['addresses'][0]['x']))

                shop = Shops.objects.create(
                    shopper_id=shopper_id,
                    shopper_name=shopper_name,
                    lat=lat,
                    lng=lng,
                    intro_image=intro_image
                )

                print(f"저장된 정보 - 이름: {shopper_name}, 주소: {address}, 전화번호: {item.get('telephone', '없음')}, 위도: {lat}, 경도: {lng}")
            else:
                print("해당 주소에 대한 좌표 변환 결과가 없습니다.")
        else:
            print("Geocoding API 요청 실패:", geocode_response.status_code)

    print("네일샵 정보가 성공적으로 데이터베이스에 저장되었습니다.")
else:
    print("API 요청 실패:", response.status_code)
