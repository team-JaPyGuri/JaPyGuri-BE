import os
import sys
import uuid
from random import randint, choice

# Django 환경 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Designs, Shops 

def create_designs():
    for _ in range(30):
        shops = Shops.objects.all()
        shop = choice(shops)  # 랜덤으로 샵 선택
        design = Designs(
            shop=shop,
            design_name=f"Design {_+1}",
            price=randint(10000, 50000),  # 10,000 ~ 50,000 사이의 랜덤 가격
            design_url=f"https://example.com/design_{_+1}.jpg",
            like_count=randint(0, 100),  
            is_active=True
        )
        design.save()
        print(f"Created design: {design.design_name}")

if __name__ == "__main__":
    create_designs()
