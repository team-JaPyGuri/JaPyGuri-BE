from django.contrib.auth import login
from nailo_BE.models import Customers
from django.utils.deprecation import MiddlewareMixin

# 고객 기준 데모 로그인 미들웨어
class DemoLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 이미 로그인된 사용자가 있으면 아무 작업도 하지 않음
        if request.user.is_authenticated:
            return

        try:
            # 데모 사용자 확인 또는 생성
            demo_user, created = Customers.objects.get_or_create(
                customer_id="demo_user",
                defaults={
                    "customer_name": "Demo User",
                    "customer_pw": "default_password"
                }
            )
        except Customers.DoesNotExist:
            # 데모 사용자 생성 (혹시 예외 발생 시)
            demo_user = Customers.objects.create(
                customer_id="demo_user",
                customer_name="Demo User",
                customer_pw="default_password"
            )

        # request.user를 데모 사용자로 설정
        request.user = demo_user
