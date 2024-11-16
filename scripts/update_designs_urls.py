import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Shops, Designs

# 네일 이미지 url 변경 코드

image_urls = [
    "",
]
# print(len(image_urls))

# URL 리스트와 shop_id 매칭하여 일괄 업데이트
for i, url in enumerate(image_urls, start=1):
    try:
        design = Designs.objects.get(design_id=i)  # shop_id가 i인 Shops 객체 가져오기
        shop.shop_url = url  # shop_url 필드에 URL 설정
        shop.save()
        print(f"Updated shop_id {i} with URL {url}")
    except Shops.DoesNotExist:
        print(f"Shop with ID {i} not found.")
