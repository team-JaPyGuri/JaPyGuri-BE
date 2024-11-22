import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")

import django
django.setup()

from nailo_be.models import Customers

def update_customer_key():
    try:
        print(f"간당")
        # customer_id가 'demo_user'인 행 찾기
        customer = Customers.objects.get(customer_id='demo_user')
        print(f"현재 customer_key: {customer.customer_key}")

        # 새로운 하이픈 없는 UUID 생성
        new_uuid = uuid.uuid4().hex
        print(f"새로 생성된 UUID (32자): {new_uuid}")

        # UUID 업데이트
        customer.customer_key = new_uuid
        customer.save()
        print(f"customer_id가 'demo_user'인 행의 customer_key가 업데이트되었습니다: {customer.customer_key}")
    except Customers.DoesNotExist:
        print("customer_id가 'demo_user'인 행을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    update_customer_key()
