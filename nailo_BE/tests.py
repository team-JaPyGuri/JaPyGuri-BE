from django.test import TestCase, Client
from django.urls import reverse
from .models import Shops, Request, Response, Customers, Designs
import json

class ShopAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 테스트용 데이터 생성
        self.customer = Customers.objects.create(
            customer_key="test_customer",
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
            price="12000",
            contents="Available"
        )

    def test_request_service(self):
        # POST /api/request-service
        url = reverse('request_service')
        request_data = {
            "customer_key": str(self.customer.customer_key),
            "design_key": str(self.design.design_key),
            "price": "10000",
            "contents": "가능 여부를 알려주세요",
        }
        response = self.client.post(url, json.dumps(request_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("message"), "Request sent successfully")
        
    def test_get_responses(self):
        # GET /api/get-responses
        url = reverse('get_responses', args=[str(self.customer.customer_key), str(self.design.design_key)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)  # 응답이 1개 있는지 확인
        self.assertIn("response_key", response.json()[0])  # 응답에 'response_key' 필드가 있는지 확인

    def test_nearby_shops(self):
        # GET /api/nearby-shops
        url = reverse('get_nearby_shops')
        response = self.client.get(url, data={'lat': 37.5665, 'lng': 126.9780})

        # 응답 데이터 확인
        response_data = response.json()
        self.assertGreaterEqual(len(response_data), 1)  # 최소 1개의 샵이 있어야 함
        self.assertIn("shopper_key", response_data[0])  
        self.assertIn("name", response_data[0])         
        self.assertIn("latitude", response_data[0])     
        self.assertIn("longitude", response_data[0])    

    def test_respond_request_accepted_with_price(self):
        # 샵이 요청을 수락하고 가격을 지정하는 경우
        url = reverse('respond_request')
        response_data = {
            "request_key": str(self.request.request_key),
            "response": "accepted",
            "price": "13000",
            "contents": "We can do it!"
        }
        response = self.client.post(url, json.dumps(response_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "accepted")
        self.assertEqual(response.json().get("message"), "Response submitted successfully")

    def test_respond_request_accepted_without_price(self):
        # 샵이 요청을 수락하지만 가격을 지정하지 않는 경우-원래 가격 사용
        url = reverse('respond_request')
        response_data = {
            "request_key": str(self.request.request_key),
            "response": "accepted",
            "contents": "We accept your request!"
        }
        response = self.client.post(url, json.dumps(response_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "accepted")
        self.assertEqual(response.json().get("message"), "Response submitted successfully")

    def test_respond_request_rejected(self):
        # 샵이 요청을 거절하는 경우
        url = reverse('respond_request')
        response_data = {
            "request_key": str(self.request.request_key),
            "response": "rejected",
            "contents": "Unfortunately, we cannot fulfill this request."
        }
        response = self.client.post(url, json.dumps(response_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "rejected")
        self.assertEqual(response.json().get("message"), "Response submitted successfully")