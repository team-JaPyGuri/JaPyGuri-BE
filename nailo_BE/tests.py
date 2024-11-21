import json
import asyncio
import logging
import uuid
from channels.testing import ChannelsLiveServerTestCase, WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from uuid import UUID

from .models import *
from nailo.asgi import application
from .routing import websocket_urlpatterns
from .utils import get_user_id

import random

logger = logging.getLogger('nailo_be.consumers')

# class WebSocketTests(ChannelsLiveServerTestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.channel_layer = get_channel_layer()
    
#     def setUp(self):
#         """동기적 셋업 - asyncSetUp 호출"""
#         super().setUp()
#         asyncio.run(self.asyncSetUp())
        
#     async def asyncSetUp(self):
#         """비동기 셋업 - 테스트에 필요한 기본 데이터 생성"""
#         self.unique_customer_id = f"test_id_{uuid.uuid4()}"
        
#         # 기본 테스트 데이터 생성
#         self.customer = await Customers.objects.acreate(
#             customer_id=self.unique_customer_id,
#             customer_pw="test_password",
#             customer_name="Test Customer"
#         )
        
#         self.shop = await Shops.objects.acreate(
#             shop_id="test_shop_id",
#             shop_name="Test Shop",
#             lat=37.5665,
#             lng=126.9780,
#             shop_url="test_image_url"
#         )
        
#         self.design = await Designs.objects.acreate(
#             shop=self.shop,
#             design_name="Test Design",
#             price=10000
#         )

#     async def test_nail_service_consumer_connect(self):
#         """웹소켓 연결 테스트"""
#         communicator = None
#         try:
#             # 로거 설정
#             logger = logging.getLogger('nailo_be.consumers')
#             logger.setLevel(logging.INFO)

#             # 연결 전에 assertLogs 시작
#             with self.assertLogs('nailo_be.consumers', level='INFO') as log:
#                 communicator = WebsocketCommunicator(
#                     application,
#                     f"/ws/shop/{self.shop.shop_key}/"
#                 )
#                 connected, _ = await communicator.connect()
#                 self.assertTrue(connected)

#                 expected_msg = f"WebSocket connection established for user: {self.shop.shop_key}"
#                 self.assertTrue(
#                     any(expected_msg in msg for msg in log.output),
#                     f"Expected log message not found in {log.output}"
#                 )
#         finally:
#             if communicator:
#                 await communicator.disconnect()
            
#     async def test_nearby_shops(self):
#         """네일샵 목록 조회 테스트"""
#         await Shops.objects.all().adelete()
#         try:
#             # 테스트용 추가 샵 생성
#             test_locations = [
#                 (37.5665, 126.9780),  # 서울 시청
#                 (37.5657, 126.9769),  # 위치 1
#                 (37.5647, 126.9758),  # 위치 2
#             ]
            
#             for i, (lat, lng) in enumerate(test_locations):
#                 shop = await Shops.objects.acreate(
#                     shop_id=f"test_shop_{i}",
#                     shop_name=f"Test Shop {i}",
#                     lat=lat,
#                     lng=lng,
#                     shop_url=f"test_image_url_{i}"
#                 )

#             # WebSocket 연결
#             communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/customer/{self.customer.customer_key}/"  # URL 형식 수정
#             )
#             connected, _ = await communicator.connect()
#             self.assertTrue(connected, "WebSocket 연결 실패")

#             # 샵 목록 조회 요청
#             await communicator.send_json_to({
#                 "action": "nearby_shops",
#                 "lat": 37.5665,
#                 "lng": 126.9780
#             })

#             # 응답 검증
#             response = await communicator.receive_json_from(timeout=5)
#             self.assertIn("type", response)
#             self.assertEqual(response["type"], "shop_list")
#             self.assertIn("shops", response)
            
#             shops = response["shops"]
#             self.assertEqual(len(shops), len(test_locations))  # 기본 생성 샵 1개 포함
            
#             # 필요한 필드들이 모두 포함되어 있는지 확인
#             expected_fields = {'shop_key', 'shop_name', 'shop_id', 'lat', 'lng', 'shop_url'}
#             for shop in shops:
#                 self.assertTrue(all(field in shop for field in expected_fields))

#         finally:
#             await communicator.disconnect()
            
#     async def test_request_service_via_websocket(self):
#         """시술 요청 테스트"""
#         try:
#             # 고객 WebSocket 연결
#             customer_communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/customer/{self.customer.customer_key}/"
#             )
#             connected, _ = await customer_communicator.connect()
#             self.assertTrue(connected, "고객 WebSocket 연결 실패")

#             # 네일샵 WebSocket 연결
#             shop_communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/shop/{self.shop.shop_key}/"
#             )
#             shop_connected, _ = await shop_communicator.connect()
#             self.assertTrue(shop_connected, "네일샵 WebSocket 연결 실패")

#             # 1. 고객이 시술 요청
#             await customer_communicator.send_json_to({
#                 "action": "request_service",
#                 "customer_key": str(self.customer.customer_key),
#                 "design_key": str(self.design.design_key),
#                 "contents": "시술 요청합니다",
#                 "status": "pending",
#             })

#             # 2. 고객이 요청 생성 완료 응답 수신
#             customer_response = await customer_communicator.receive_json_from(timeout=5)
#             self.assertEqual(customer_response["status"], "pending")
#             self.assertEqual(customer_response["message"], "시술 요청이 완료되었습니다.")

#             # 3. 네일샵이 푸시 알림 수신
#             shop_notification = await shop_communicator.receive_json_from(timeout=5)
#             self.assertEqual(shop_notification["type"], "new_request")

#             # 4. DB에 Request가 생성되었는지 확인
#             request = await Request.objects.filter(
#                 customer=self.customer,
#                 shop=self.shop,
#                 design=self.design,
#                 status="pending",
#                 contents="시술 요청합니다"
#             ).afirst()
#             self.assertIsNotNone(request, "Request 객체가 생성되지 않았습니다")
#             self.assertEqual(request.price, self.design.price)  # 기본 가격 확인

#         finally:
#             await customer_communicator.disconnect()
#             await shop_communicator.disconnect()

#     async def test_respond_service_via_websocket(self):
#         """시술 요청 응답 테스트"""
#         try:
#             # 1. 먼저 Request 생성
#             request = await Request.objects.acreate(
#                 customer=self.customer,
#                 shop=self.shop,
#                 design=self.design,
#                 price=self.design.price,
#                 status="pending"
#             )

#             # 2. WebSocket 연결
#             customer_communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/customer/{self.customer.customer_key}/"
#             )
#             shop_communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/shop/{self.shop.shop_key}/"
#             )

#             await customer_communicator.connect()
#             await shop_communicator.connect()

#             # 3. 네일샵이 수락 응답
#             new_price = self.design.price + 5000  # 가격 변경
#             await shop_communicator.send_json_to({
#                 "action": "respond_service",
#                 "request_key": str(request.request_key),
#                 "price": new_price,
#                 "status": "accepted", 
#                 "contents": "네, 가능합니다!"
#             })

#             # 4. 네일샵이 응답 완료 메시지 수신
#             shop_response = await shop_communicator.receive_json_from(timeout=5)
#             self.assertEqual(shop_response["type"], "completed_response")
#             self.assertEqual(shop_response["status"], "accepted")
            
#             # response_data 확인
#             response_data = shop_response["response_data"]
#             self.assertEqual(response_data["shop_name"], self.shop.shop_name)
#             self.assertEqual(response_data["price"], new_price)
#             self.assertEqual(response_data["contents"], "네, 가능합니다!")

#             # 5. 고객이 푸시 알림 수신
#             customer_notification = await customer_communicator.receive_json_from(timeout=5)
#             self.assertEqual(customer_notification["type"], "new_response")
#             self.assertEqual(customer_notification["request_key"], str(request.request_key))
#             self.assertEqual(customer_notification["shop_name"], self.shop.shop_name)

#         finally:
#             await customer_communicator.disconnect()
#             await shop_communicator.disconnect()

#     async def test_reject_service_via_websocket(self):
#         """시술 요청 거절 테스트"""
#         try:
#             # 1. Request 생성
#             request = await Request.objects.acreate(
#                 customer=self.customer,
#                 shop=self.shop,
#                 design=self.design,
#                 price=self.design.price,
#                 status="pending"
#             )

#             # 2. WebSocket 연결
#             customer_communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/customer/{self.customer.customer_key}/"
#             )
#             shop_communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/shop/{self.shop.shop_key}/"
#             )

#             await customer_communicator.connect()
#             await shop_communicator.connect()

#             # 3. 네일샵이 거절 응답
#             await shop_communicator.send_json_to({
#                 "action": "respond_service",
#                 "request_key": str(request.request_key),
#                 "status": "rejected",
#                 "contents": "죄송합니다. 해당 시간에는 불가능합니다."
#             })

#             # 4. 네일샵이 응답 완료 메시지 수신
#             shop_response = await shop_communicator.receive_json_from(timeout=5)
#             self.assertEqual(shop_response["type"], "completed_response")
#             self.assertEqual(shop_response["status"], "rejected")
            
#             # response_data 확인
#             response_data = shop_response["response_data"]
#             self.assertEqual(response_data["shop_name"], self.shop.shop_name)
#             self.assertEqual(response_data["contents"], "죄송합니다. 해당 시간에는 불가능합니다.")

#             # 5. 고객이 푸시 알림 수신
#             customer_notification = await customer_communicator.receive_json_from(timeout=5)
#             self.assertEqual(customer_notification["type"], "new_response")
#             self.assertEqual(customer_notification["shop_name"], self.shop.shop_name)
#             self.assertEqual(customer_notification["request_key"], str(request.request_key))

#         finally:
#             await customer_communicator.disconnect()
#             await shop_communicator.disconnect()

#     async def test_get_response_list(self):
#         """응답 목록 조회 테스트"""
#         try:
#             # 디자인 생성
#             design1 = await Designs.objects.acreate(
#                 shop=self.shop,
#                 design_name="Test Design 1",
#                 price=10000
#             )

#             # Request 생성
#             request = await Request.objects.acreate(
#                 customer=self.customer,
#                 shop=self.shop,
#                 design=design1,
#                 price=8000,  # 고객 희망가
#                 contents="손톱이 약해서 조심스럽게 시술 부탁드려요",  # 고객 요청사항
#                 status="accepted"
#             )

#             # Response 생성
#             response = await Response.objects.acreate(
#                 request=request,
#                 customer=self.customer,
#                 shop=self.shop,
#                 price=10000,  # 샵 제시가
#                 contents="네, 손톱 보강 처리 포함해서 시술하겠습니다"  # 샵 응답
#             )
#             communicator = None
            
#             # WebSocket 연결
#             communicator = WebsocketCommunicator(
#                 application,
#                 f"/ws/customer/{self.customer.customer_key}/"
#             )
#             connected, _ = await communicator.connect()
#             self.assertTrue(connected)

#             # 응답 목록 조회 요청
#             await communicator.send_json_to({
#                 "action": "get_responses",
#                 "customer_key": str(self.customer.customer_key)
#             })

#             # 응답 확인
#             ws_response = await communicator.receive_json_from(timeout=5)
#             self.assertEqual(ws_response["type"], "response_list")
            
#             # 디자인 목록 확인
#             designs = ws_response["designs"]
#             self.assertEqual(len(designs), 1)
            
#             # 디자인 정보 확인
#             design = designs[0]
#             self.assertEqual(design["design_key"], str(design1.design_key))
#             self.assertEqual(design["design_name"], design1.design_name)
            
#             # 샵 요청 목록 확인
#             shop_requests = design["shop_requests"]
#             self.assertEqual(len(shop_requests), 1)
            
#             # 샵 정보 확인
#             shop_request = shop_requests[0]
#             self.assertEqual(shop_request["shop_name"], self.shop.shop_name)
            
#             # 요청 상세 정보 확인
#             request_details = shop_request["request_details"]
#             self.assertEqual(len(request_details), 1)
            
#             request_detail = request_details[0]
#             # 기본 정보 확인
#             self.assertEqual(request_detail["request_key"], str(request.request_key))
#             self.assertEqual(request_detail["status"], "accepted")
            
#             # 고객 요청 정보 확인
#             customer_request = request_detail["request"]
#             self.assertEqual(customer_request["price"], 8000)
#             self.assertEqual(customer_request["contents"], "손톱이 약해서 조심스럽게 시술 부탁드려요")
            
#             # 샵 응답 정보 확인
#             shop_response = request_detail["response"]
#             self.assertIsNotNone(shop_response)
#             self.assertEqual(shop_response["response_key"], str(response.response_key))
#             self.assertEqual(shop_response["price"], 10000)
#             self.assertEqual(shop_response["contents"], "네, 손톱 보강 처리 포함해서 시술하겠습니다")
#             self.assertIsNotNone(shop_response["created_at"])

#         except Exception as e:
#             self.fail(f"테스트 실패: {str(e)}")
#         finally:
#             await communicator.disconnect()
            
#     async def asyncTearDown(self):
#         """테스트 데이터 정리"""
#         await database_sync_to_async(self.customer.delete)()
#         await database_sync_to_async(self.shop.delete)()
#         await database_sync_to_async(self.design.delete)()

class GetUserIdTests(TestCase):
    def setUp(self):
        # 테스트용 Customer와 Shop 객체 생성
        self.customer = Customers.objects.create(
            customer_id="test_customer",
            customer_name="Test Customer",
        )

        self.shop = Shops.objects.create(
            shop_id="test_shop",
            shop_name="Test Shop",
            lat=37.5665,
            lng=126.9780,
            shop_url="http://example.com",
        )

    def test_get_customer_by_id(self):
        """Customer를 user_type과 user_id로 가져오는 테스트"""
        user, user_type = get_user_id("customer", self.customer.customer_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.customer_id, self.customer.customer_id)
        self.assertEqual(user.customer_name, self.customer.customer_name)

    def test_get_shop_by_id(self):
        """Shop을 user_type과 user_id로 가져오는 테스트"""
        user, user_type = get_user_id("shop", self.shop.shop_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.shop_id, self.shop.shop_id)

    def test_invalid_user_type(self):
        """잘못된 user_type으로 호출했을 때 None 반환 테스트"""
        result = get_user_id("invalid_type", self.customer.customer_id)
        self.assertIsNone(result)  # user가 None인지 확인
        self.assertIsNone(result)  # user_type이 None인지 확인

    def test_nonexistent_user_id(self):
        """존재하지 않는 user_id로 호출했을 때 None 반환 테스트"""
        user, user_type = get_user_id("customer", "nonexistent_id")
        self.assertIsNone(user, user_type)

class HomePageViewTests(APITestCase):
    @classmethod
    def setUp(self):
        # 테스트용 데이터 생성
        self.shop = Shops.objects.create(
            shop_id="test_shop",
            shop_name="Test Shop",
            lat=37.5665,
            lng=126.9780,
            shop_url="http://example.com"
        )
        
        for i in range(25):  
            Designs.objects.create(
                design_name=f"Design {i+1}",
                shop=self.shop,
                price=(i + 1) * 1000,
                like_count=i,
                design_url=f"http://example.com/design{i+1}.jpg",
                is_active=True,
            )

    def test_random_designs(self):
        """랜덤 9개의 디자인을 반환하는 API 테스트"""
        response = self.client.get('/api/home/', {'type': 'random'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)  

    def test_paginated_designs_first_page(self):
        """전체 디자인의 첫 번째 페이지 반환 API 테스트"""
        response = self.client.get('/api/home/', {'type': 'all', 'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 페이지네이션 데이터 확인
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)

        # 첫 페이지에 10개의 디자인이 있어야 함
        self.assertEqual(len(response.data['results']), 10)

    def test_paginated_designs_last_page(self):
        """전체 디자인의 마지막 페이지 반환 API 테스트"""
        response = self.client.get('/api/home/', {'type': 'all', 'page': 3, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 마지막 페이지에는 10개가 아닌 10개 이하의 디자인이 있을 수 있음
        self.assertLessEqual(len(response.data['results']), 10)

    def test_invalid_type(self):
        """잘못된 type 파라미터 처리 테스트"""
        response = self.client.get('/api/home/', {'type': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_no_type_defaults_to_random(self):
        """type 파라미터가 없을 때 기본값으로 랜덤 9개를 반환"""
        response = self.client.get('/api/home/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)
                
class DesignTests(APITestCase):
    @classmethod
    # 각 한 번만 생성
    def setUpTestData(cls):
        cls.customer = Customers.objects.create(
            customer_id="test_customer",
            customer_name="Test Customer"
        )
        cls.shop = Shops.objects.create(
            shop_id="test_shop_id",
            shop_name="Test Shop",
            lat=37.5665,
            lng=126.9780,
            shop_url="test_image_url"
        )
        cls.design = Designs.objects.create(
            shop=cls.shop,
            design_name="Test Design",
            price=1000,
            like_count=0,
            is_active=True
        )
        cls.like = Like.objects.create(
            customer=cls.customer,
            design=cls.design
        )

    def test_like_list(self):
        """좋아요 리스트가 존재할 때"""
        # HTTP GET 요청
        response = self.client.get(
            '/api/like-list/',
            HTTP_X_USER_TYPE='customer',  
            HTTP_X_USER_ID=self.customer.customer_id,
        )

        print("like_list: ", response)
        self.assertEqual(response.status_code, 200) 
        self.assertIn("Test Design", response.data[0]["design_name"])  
        self.assertEqual(response.data[0]["price"], 1000)

    # def test_like_list_empty(self):
    #     """좋아요 리스트가 비어 있을 때"""
    #     response = self.client.get(
    #         '/api/like-list/',
    #         HTTP_X_USER_TYPE='customer',
    #         HTTP_X_USER_ID=self.customer.customer_id,
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data, {"message": "좋아요 내역이 없습니다."})
        
    def test_design_detail(self):
        """디자인 상세 페이지 테스트"""
        response = self.client.get(
            f'/api/nail-design/{self.design.design_key}/',
            HTTP_X_USER_TYPE='customer',
            HTTP_X_USER_ID=self.customer.customer_id,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["design_name"], self.design.design_name)

class LikeToggleTests(APITestCase):
    def setUp(self):
        """테스트 데이터 생성"""
        self.customer = Customers.objects.create(
            customer_id='test_user',
            customer_name='Test User'
        )

        self.shop = Shops.objects.create(
            shop_id="test_shop",
            shop_name="Test Shop",
            lat=37.5665,
            lng=126.9780,
            shop_url="test_image_url"
        )
        
        # 테스트 디자인 생성
        self.design = Designs.objects.create(
            shop=self.shop,
            design_name='Test Design',
            price=1000,
            like_count=0,
            is_active=True
        )

    def test_like_toggle_add(self):
        """좋아요 추가 테스트"""
        response = self.client.post(
            f'/api/like-toggle/{self.design.design_key}/',
            HTTP_X_USER_TYPE='customer',
            HTTP_X_USER_ID=self.customer.customer_id,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"message": "좋아요가 추가되었습니다.", "like_count": 1})

    def test_like_toggle_remove(self):
        """좋아요 취소 테스트"""
        # 먼저 좋아요 추가
        Like.objects.create(customer=self.customer, design=self.design)
        self.design.like_count = 1
        self.design.save()
        
        response = self.client.post(
            f'/api/like-toggle/{self.design.design_key}/',
            HTTP_X_USER_TYPE='customer',
            HTTP_X_USER_ID=self.customer.customer_id,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "좋아요가 취소되었습니다.")
        self.assertEqual(response.data["like_count"], 0)