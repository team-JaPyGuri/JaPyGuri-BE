import json
import asyncio
import logging
import uuid
from channels.testing import ChannelsLiveServerTestCase, WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from uuid import UUID

from .models import Shops, Request, Response, Customers, Designs
from nailo.asgi import application
from .routing import websocket_urlpatterns

logger = logging.getLogger('nailo_be.consumers')

class WebSocketTests(ChannelsLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.channel_layer = get_channel_layer()
    
    def setUp(self):
        """동기적 셋업 - asyncSetUp 호출"""
        super().setUp()
        asyncio.run(self.asyncSetUp())
        
    async def asyncSetUp(self):
        """비동기 셋업 - 테스트에 필요한 기본 데이터 생성"""
        self.unique_customer_id = f"test_id_{uuid.uuid4()}"
        
        # 기본 테스트 데이터 생성
        self.customer = await Customers.objects.acreate(
            customer_id=self.unique_customer_id,
            customer_pw="test_password",
            customer_name="Test Customer"
        )
        
        self.shop = await Shops.objects.acreate(
            shop_id="test_shop_id",
            shop_name="Test Shop",
            lat=37.5665,
            lng=126.9780,
            shop_url="test_image_url"
        )
        
        self.design = await Designs.objects.acreate(
            shop=self.shop,
            design_name="Test Design",
            price=10000
        )

    async def test_nail_service_consumer_connect(self):
        """웹소켓 연결 테스트"""
        communicator = None
        try:
            # 로거 설정
            logger = logging.getLogger('nailo_be.consumers')
            logger.setLevel(logging.INFO)

            # 연결 전에 assertLogs 시작
            with self.assertLogs('nailo_be.consumers', level='INFO') as log:
                communicator = WebsocketCommunicator(
                    application,
                    f"/ws/shop/{self.shop.shop_key}/"
                )
                connected, _ = await communicator.connect()
                self.assertTrue(connected)

                expected_msg = f"WebSocket connection established for user: {self.shop.shop_key}"
                self.assertTrue(
                    any(expected_msg in msg for msg in log.output),
                    f"Expected log message not found in {log.output}"
                )
        finally:
            if communicator:
                await communicator.disconnect()
            
    async def test_nearby_shops(self):
        """네일샵 목록 조회 테스트"""
        await Shops.objects.all().adelete()
        try:
            # 테스트용 추가 샵 생성
            test_locations = [
                (37.5665, 126.9780),  # 서울 시청
                (37.5657, 126.9769),  # 위치 1
                (37.5647, 126.9758),  # 위치 2
            ]
            
            for i, (lat, lng) in enumerate(test_locations):
                shop = await Shops.objects.acreate(
                    shop_id=f"test_shop_{i}",
                    shop_name=f"Test Shop {i}",
                    lat=lat,
                    lng=lng,
                    shop_url=f"test_image_url_{i}"
                )

            # WebSocket 연결
            communicator = WebsocketCommunicator(
                application,
                f"/ws/customer/{self.customer.customer_key}/"  # URL 형식 수정
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected, "WebSocket 연결 실패")

            # 샵 목록 조회 요청
            await communicator.send_json_to({
                "action": "nearby_shops",
                "lat": 37.5665,
                "lng": 126.9780
            })

            # 응답 검증
            response = await communicator.receive_json_from(timeout=5)
            self.assertIn("type", response)
            self.assertEqual(response["type"], "shop_list")
            self.assertIn("shops", response)
            
            shops = response["shops"]
            self.assertEqual(len(shops), len(test_locations))  # 기본 생성 샵 1개 포함
            
            # 필요한 필드들이 모두 포함되어 있는지 확인
            expected_fields = {'shop_key', 'shop_name', 'shop_id', 'lat', 'lng', 'shop_url'}
            for shop in shops:
                self.assertTrue(all(field in shop for field in expected_fields))

        finally:
            await communicator.disconnect()
            
    async def test_request_service_via_websocket(self):
        """시술 요청 테스트"""
        try:
            # 고객 WebSocket 연결
            customer_communicator = WebsocketCommunicator(
                application,
                f"/ws/customer/{self.customer.customer_key}/"
            )
            connected, _ = await customer_communicator.connect()
            self.assertTrue(connected, "고객 WebSocket 연결 실패")

            # 네일샵 WebSocket 연결
            shop_communicator = WebsocketCommunicator(
                application,
                f"/ws/shop/{self.shop.shop_key}/"
            )
            shop_connected, _ = await shop_communicator.connect()
            self.assertTrue(shop_connected, "네일샵 WebSocket 연결 실패")

            # 1. 고객이 시술 요청
            await customer_communicator.send_json_to({
                "action": "request_service",
                "customer_key": str(self.customer.customer_key),
                "design_key": str(self.design.design_key),
                "contents": "시술 요청합니다",
                "status": "pending",
            })

            # 2. 고객이 요청 생성 완료 응답 수신
            customer_response = await customer_communicator.receive_json_from(timeout=5)
            self.assertEqual(customer_response["status"], "pending")
            self.assertEqual(customer_response["message"], "시술 요청이 완료되었습니다.")

            # 3. 네일샵이 푸시 알림 수신
            shop_notification = await shop_communicator.receive_json_from(timeout=5)
            self.assertEqual(shop_notification["type"], "new_request")

            # 4. DB에 Request가 생성되었는지 확인
            request = await Request.objects.filter(
                customer=self.customer,
                shop=self.shop,
                design=self.design,
                status="pending",
                contents="시술 요청합니다"
            ).afirst()
            self.assertIsNotNone(request, "Request 객체가 생성되지 않았습니다")
            self.assertEqual(request.price, self.design.price)  # 기본 가격 확인

        finally:
            await customer_communicator.disconnect()
            await shop_communicator.disconnect()

    async def test_respond_service_via_websocket(self):
        """시술 요청 응답 테스트"""
        try:
            # 1. 먼저 Request 생성
            request = await Request.objects.acreate(
                customer=self.customer,
                shop=self.shop,
                design=self.design,
                price=self.design.price,
                status="pending"
            )

            # 2. WebSocket 연결
            customer_communicator = WebsocketCommunicator(
                application,
                f"/ws/customer/{self.customer.customer_key}/"
            )
            shop_communicator = WebsocketCommunicator(
                application,
                f"/ws/shop/{self.shop.shop_key}/"
            )

            await customer_communicator.connect()
            await shop_communicator.connect()

            # 3. 네일샵이 수락 응답
            new_price = self.design.price + 5000  # 가격 변경
            await shop_communicator.send_json_to({
                "action": "respond_service",
                "request_key": str(request.request_key),
                "price": new_price,
                "status": "accepted", 
                "contents": "네, 가능합니다!"
            })

            # 4. 네일샵이 응답 완료 메시지 수신
            shop_response = await shop_communicator.receive_json_from(timeout=5)
            self.assertEqual(shop_response["type"], "completed_response")
            self.assertEqual(shop_response["status"], "accepted")
            
            # response_data 확인
            response_data = shop_response["response_data"]
            self.assertEqual(response_data["shop_name"], self.shop.shop_name)
            self.assertEqual(response_data["price"], new_price)
            self.assertEqual(response_data["contents"], "네, 가능합니다!")

            # 5. 고객이 푸시 알림 수신
            customer_notification = await customer_communicator.receive_json_from(timeout=5)
            self.assertEqual(customer_notification["type"], "new_response")
            self.assertEqual(customer_notification["request_key"], str(request.request_key))
            self.assertEqual(customer_notification["shop_name"], self.shop.shop_name)

        finally:
            await customer_communicator.disconnect()
            await shop_communicator.disconnect()

    async def test_reject_service_via_websocket(self):
        """시술 요청 거절 테스트"""
        try:
            # 1. Request 생성
            request = await Request.objects.acreate(
                customer=self.customer,
                shop=self.shop,
                design=self.design,
                price=self.design.price,
                status="pending"
            )

            # 2. WebSocket 연결
            customer_communicator = WebsocketCommunicator(
                application,
                f"/ws/customer/{self.customer.customer_key}/"
            )
            shop_communicator = WebsocketCommunicator(
                application,
                f"/ws/shop/{self.shop.shop_key}/"
            )

            await customer_communicator.connect()
            await shop_communicator.connect()

            # 3. 네일샵이 거절 응답
            await shop_communicator.send_json_to({
                "action": "respond_service",
                "request_key": str(request.request_key),
                "status": "rejected",
                "contents": "죄송합니다. 해당 시간에는 불가능합니다."
            })

            # 4. 네일샵이 응답 완료 메시지 수신
            shop_response = await shop_communicator.receive_json_from(timeout=5)
            self.assertEqual(shop_response["type"], "completed_response")
            self.assertEqual(shop_response["status"], "rejected")
            
            # response_data 확인
            response_data = shop_response["response_data"]
            self.assertEqual(response_data["shop_name"], self.shop.shop_name)
            self.assertEqual(response_data["contents"], "죄송합니다. 해당 시간에는 불가능합니다.")

            # 5. 고객이 푸시 알림 수신
            customer_notification = await customer_communicator.receive_json_from(timeout=5)
            self.assertEqual(customer_notification["type"], "new_response")
            self.assertEqual(customer_notification["shop_name"], self.shop.shop_name)
            self.assertEqual(customer_notification["request_key"], str(request.request_key))

        finally:
            await customer_communicator.disconnect()
            await shop_communicator.disconnect()

    async def test_get_response_list(self):
        """응답 목록 조회 테스트"""
        try:
            # 디자인 생성
            design1 = await Designs.objects.acreate(
                shop=self.shop,
                design_name="Test Design 1",
                price=10000
            )

            # Request 생성
            request = await Request.objects.acreate(
                customer=self.customer,
                shop=self.shop,
                design=design1,
                price=8000,  # 고객 희망가
                contents="손톱이 약해서 조심스럽게 시술 부탁드려요",  # 고객 요청사항
                status="accepted"
            )

            # Response 생성
            response = await Response.objects.acreate(
                request=request,
                customer=self.customer,
                shop=self.shop,
                price=10000,  # 샵 제시가
                contents="네, 손톱 보강 처리 포함해서 시술하겠습니다"  # 샵 응답
            )
            communicator = None
            
            # WebSocket 연결
            communicator = WebsocketCommunicator(
                application,
                f"/ws/customer/{self.customer.customer_key}/"
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)

            # 응답 목록 조회 요청
            await communicator.send_json_to({
                "action": "get_responses",
                "customer_key": str(self.customer.customer_key)
            })

            # 응답 확인
            ws_response = await communicator.receive_json_from(timeout=5)
            self.assertEqual(ws_response["type"], "response_list")
            
            # 디자인 목록 확인
            designs = ws_response["designs"]
            self.assertEqual(len(designs), 1)
            
            # 디자인 정보 확인
            design = designs[0]
            self.assertEqual(design["design_key"], str(design1.design_key))
            self.assertEqual(design["design_name"], design1.design_name)
            
            # 샵 요청 목록 확인
            shop_requests = design["shop_requests"]
            self.assertEqual(len(shop_requests), 1)
            
            # 샵 정보 확인
            shop_request = shop_requests[0]
            self.assertEqual(shop_request["shop_name"], self.shop.shop_name)
            
            # 요청 상세 정보 확인
            request_details = shop_request["request_details"]
            self.assertEqual(len(request_details), 1)
            
            request_detail = request_details[0]
            # 기본 정보 확인
            self.assertEqual(request_detail["request_key"], str(request.request_key))
            self.assertEqual(request_detail["status"], "accepted")
            
            # 고객 요청 정보 확인
            customer_request = request_detail["request"]
            self.assertEqual(customer_request["price"], 8000)
            self.assertEqual(customer_request["contents"], "손톱이 약해서 조심스럽게 시술 부탁드려요")
            
            # 샵 응답 정보 확인
            shop_response = request_detail["response"]
            self.assertIsNotNone(shop_response)
            self.assertEqual(shop_response["response_key"], str(response.response_key))
            self.assertEqual(shop_response["price"], 10000)
            self.assertEqual(shop_response["contents"], "네, 손톱 보강 처리 포함해서 시술하겠습니다")
            self.assertIsNotNone(shop_response["created_at"])

        except Exception as e:
            self.fail(f"테스트 실패: {str(e)}")
        finally:
            await communicator.disconnect()
            
    async def asyncTearDown(self):
        """테스트 데이터 정리"""
        await database_sync_to_async(self.customer.delete)()
        await database_sync_to_async(self.shop.delete)()
        await database_sync_to_async(self.design.delete)()