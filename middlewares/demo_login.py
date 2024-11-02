from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin

# 고객 기준
class DemoLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        customer = get_user_model()
        try:
            demo_user = User.objects.get(customer_id="demo_user")  # 가정된 사용자로 설정할 ID
        except User.DoesNotExist:
            demo_user = User.objects.create(
                customer_id="demo_user",
                customer_name="Demo User",
                customer_pw="default_password",
            )

        request.user = demo_user
