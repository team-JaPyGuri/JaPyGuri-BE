from django.test import TestCase, Client
from django.urls import reverse
from uuid import UUID
from .models import Shops, Request, Response, Customers, Designs
import json

# Request와 Response 객체가 미리 생성되어 있어야 하는 테스트 클래스
class RequireTests(TestCase):
    def setUp(self):
        # 공통 데이터 생성
        self.client = Client()
        self.customer = Customers.objects.create(
            customer_id="test_id",
            customer_pw="test_password",
            customer_name="Test Customer"
        )

        self.shop = Shops.objects.create(
            shopper_id="shop_id",
            shopper_name="Test Shop",
            lat=37.5665,
            lng=126.9780,
            shops_url="test_image_url"
        )
        
        self.design = Designs.objects.create(
            shop=self.shop,
            design_name="Test Design",
            price=10000
        )

        # 미리 Request와 Response 객체를 생성
        self.request = Request.objects.create(
            customer=self.customer,
            shop=self.shop,
            design=self.design,
            price=10000,
            status="pending"
        )

        self.response = Response.objects.create(
            customer=self.customer,
            shop=self.shop,
            request=self.request,
            price=10000,
            contents="We can do it!"
        )

    def test_get_responses(self):
        url = reverse('nail-service-get-responses', args=[str(self.customer.customer_key), str(self.design.design_key)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertIn("response_key", response.json()[0])

    def test_respond_request_accepted_with_price(self):
        url = reverse('nail-service-respond-service')
        response_data = {
            "request_key": str(self.request.request_key),
            "response": "accepted",
            "price": 1300,
            "contents": "We can do it!"
        }
        response = self.client.post(url, json.dumps(response_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "accepted")
        self.assertEqual(response.json().get("message"), "Response submitted successfully")

    def test_respond_request_accepted_without_price(self):
        url = reverse('nail-service-respond-service')
        response_data = {
            "request_key": str(self.request.request_key),
            "response": "accepted",
            "price": 10000,
            "contents": "We accept your request!"
        }
        response = self.client.post(url, json.dumps(response_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "accepted")
        self.assertEqual(response.json().get("message"), "Response submitted successfully")

    def test_respond_request_rejected(self):
        url = reverse('nail-service-respond-service')
        response_data = {
            "request_key": str(self.request.request_key),
            "response": "rejected",
            "price": 10000,
            "contents": "Unfortunately, we cannot fulfill this request."
        }
        response = self.client.post(url, json.dumps(response_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "rejected")
        self.assertEqual(response.json().get("message"), "Response submitted successfully")


# Request와 Response 객체가 미리 생성되어 있을 필요가 없는 테스트 클래스
class NotRequireTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customers.objects.create(
            customer_id="test_id",
            customer_pw="test_password",
            customer_name="Test Customer"
        )

        self.shop = Shops.objects.create(
            shopper_id="shop_id",
            shopper_name="Test Shop",
            lat=37.5665,
            lng=126.9780,
            shops_url="test_image_url"
        )
        
        self.design = Designs.objects.create(
            shop=self.shop,
            design_name="Test Design",
            price=10000
        )

    def test_nearby_shops(self):
        url = reverse('nail-service-nearby-shops')
        response = self.client.get(url, data={'lat': 37.5665, 'lng': 126.9780})
        response_data = response.json()
        self.assertGreaterEqual(len(response_data), 1)
        self.assertIn("shopper_key", response_data[0])
        self.assertIn("shopper_name", response_data[0])
        self.assertIn("lat", response_data[0])
        self.assertIn("lng", response_data[0])

    def test_request_service(self):
        url = reverse('nail-service-request-service')
        request_data = {
            "customer_key": str(self.customer.customer_key),
            "design_key": str(self.design.design_key),
            "price": 10000,
            "contents": "가능 여부를 알려주세요",
        }
        response = self.client.post(
            url,
            json.dumps(request_data),
            content_type="application/json",
            HTTP_TEST_MODE="true"
        )
        self.assertEqual(response.status_code, 200, "응답 코드가 200이 아닙니다.")
        self.assertEqual(response.json().get("status"), "success", "응답 상태가 'success'가 아닙니다.")
        
        # Request 객체가 데이터베이스에 저장되었는지 확인
        request_instance = Request.objects.filter(
            customer=self.customer,
            shop=self.shop,
            design=self.design,
            price=10000,
            status="pending",
            contents="가능 여부를 알려주세요"
        )
        
        # Request 인스턴스가 1개 저장되었는지 확인
        self.assertEqual(request_instance.count(), 1, "Request 객체가 1개 저장되지 않았습니다.")
        
        # 생성된 Request 인스턴스 내용 확인
        created_request = request_instance.first()
        self.assertEqual(created_request.contents, "가능 여부를 알려주세요", "Request의 'contents' 필드가 예상과 다릅니다.")
        self.assertEqual(created_request.price, 10000, "Request의 'price' 필드가 예상과 다릅니다.")
        self.assertEqual(created_request.status, "pending", "Request의 'status' 필드가 예상과 다릅니다.")