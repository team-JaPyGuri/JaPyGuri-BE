import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from .models import Request, Response, Designs, Shops, Customers
from .serializers import RequestSerializer, ResponseSerializer, AddRequestSerializer, ResponseListSerializer
from .utils import get_user_id

logger = logging.getLogger('nailo_be.consumers')

class NailServiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # 헤더에서 사용자 타입과 ID 가져오기
            headers = dict(self.scope['headers'])
            user_type = headers.get(b'x-user-type', b'').decode('utf-8')
            user_id = headers.get(b'x-user-id', b'').decode('utf-8')

            # 그룹 이름 설정
            self.group_name = f"{user_type}_{user_id}"
            
            # 사용자 객체 가져오기
            user, user_type = await database_sync_to_async(get_user_id)(user_type, user_id)
            self.user = user
            self.user_type = user_type
            
            # 그룹에 추가
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

            logger.info(f"WebSocket connection established for {user_type}: {user_id}")
        except ValueError as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close()
        except Exception as e:
            logger.error(f"Unexpected error during WebSocket connection: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        # 그룹에서 제거
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket connection closed for {self.user_type}: {self.user.customer_id if self.user_type == 'customer' else self.user.shop_id}")

    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "nearby_shops":
                await self.handle_nearby_shops(data)
            elif action == "request_service":
                await self.handle_service_request(data)
            elif action == "respond_service":
                await self.handle_service_response(data)
            elif action == "get_responses":
                await self.handle_get_responses(data)
            else:
                await self.send(text_data=json.dumps({
                    "error": f"Unknown action: {action}"
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))

    async def handle_nearby_shops(self, data):
        """활성화된 모든 네일샵 정보 제공"""
        try:
            # 활성화된 모든 샵 조회
            shops = await database_sync_to_async(list)(
                Shops.objects.filter(is_active=True).values(
                    'shop_key',
                    'shop_name',
                    'shop_id',
                    'lat',
                    'lng',
                    'shop_url'
                )
            )

            # UUID는 JSON 직렬화가 안 되므로 문자열로 변환
            for shop in shops:
                shop['shop_key'] = str(shop['shop_key'])
                # Decimal 타입의 위도/경도를 float로 변환
                shop['lat'] = float(shop['lat'])
                shop['lng'] = float(shop['lng'])

            await self.send(text_data=json.dumps({
                "type": "shop_list",
                "shops": shops
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))
        
    async def handle_service_request(self, data):
        """시술 요청 처리"""
        try:
            serializer = RequestSerializer(data=data)
            if not serializer.is_valid():
                await self.send(text_data=json.dumps({
                    "error": serializer.errors
                }))
                return

            # 데이터 검증
            customer = await database_sync_to_async(Customers.objects.get)(
                customer_key=serializer.validated_data['customer_key']
            )
            design = await database_sync_to_async(Designs.objects.get)(
                design_key=serializer.validated_data['design_key']
            )
            shop = await database_sync_to_async(lambda: design.shop)()

            # Request 생성
            request = await database_sync_to_async(Request.objects.create)(
                customer=customer,
                shop=shop,
                design=design,
                price=design.price,  
                status="pending",   
                contents=serializer.validated_data.get('contents', '')
            )

            # 시리얼라이즈
            request_serializer = AddRequestSerializer(request)
            request_data = await database_sync_to_async(lambda: request_serializer.data)()

            # 네일샵에 알림 전송
            await self.channel_layer.group_send(
                f"shop_{shop.shop_key}",
                {
                    "type": "notify_shop_new_request",
                    "request_key": str(request.request_key),
                }
            )

            # 요청자에게 응답
            await self.send(text_data=json.dumps({
                "type": "completed_request",
                "status": "pending",
                "message": "시술 요청이 완료되었습니다."
            }))

        except (Customers.DoesNotExist, Designs.DoesNotExist) as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))

    async def handle_service_response(self, data):
        """시술 응답 처리"""
        try:
            serializer = ResponseSerializer(data=data)
            if not serializer.is_valid():
                await self.send(text_data=json.dumps({
                    "error": serializer.errors
                }))
                return

            request = await database_sync_to_async(Request.objects.get)(
                request_key=data['request_key']
            )

            response_status = serializer.validated_data['status']
            
            if response_status not in ['accepted', 'rejected']:
                await self.send(text_data=json.dumps({
                    "error": "Invalid response status"
                }))
                return

            # Request 상태 업데이트
            request.status = response_status
            await database_sync_to_async(request.save)()

            # Response 객체 생성
            @database_sync_to_async
            def create_response():
                return Response.objects.create(
                    request=request,
                    customer=request.customer,
                    shop=request.shop,
                    price=data.get('price', request.price),
                    contents=serializer.validated_data.get('contents', '')
                )

            response = await create_response()

            # response_data 생성
            response_data = {
                "shop_name": response.shop.shop_name,
                "price": response.price,
                "contents": response.contents
            }

            # 1. 네일샵에게 응답
            await self.send(text_data=json.dumps({
                "type": "completed_response",
                "status": response_status,
                "response_data": response_data
            }))

            # 2. 고객에게 새 응답 알림 
            await self.channel_layer.group_send(
                f"customer_{request.customer.customer_key}",
                {
                    "type": "notify_customer_new_response",
                    "request_key": str(request.request_key),
                    "shop_name": response.shop.shop_name
                }
            )
            
        except Request.DoesNotExist:
            await self.send(text_data=json.dumps({
                "error": "Request not found"
            }))
            
    async def notify_customer_request_sent(self, event):
        """1. 고객의 요청이 정상적으로 전송되었음을 고객에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "completed_request",
            "status": "pending",
            "request_data": event["response_data"]
        }))

    async def notify_shop_response_sent(self, event):
        """2. 샵의 응답이 정상적으로 전송되었음을 샵에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "completed_response",
            "status": event["status"],
            "response_data": event["response_data"]
        }))

    async def notify_shop_new_request(self, event):
        """3. 고객의 요청이 도착했음을 샵에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "new_request",
            "request_key": event["request_key"]
        }))

    async def notify_customer_new_response(self, event):
        """4. 샵의 응답이 도착했음을 고객에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "new_response",
            "shop_name": event["shop_name"],
            "request_key": event["request_key"]
        }))
        
    async def handle_get_responses(self, data):
        """디자인별 응답 목록 조회"""
        try:
            customer_key = data.get('customer_key')
            if not customer_key:
                await self.send(text_data=json.dumps({
                    "error": "Customer key is required"
                }))
                return

            # 고객의 모든 요청을 디자인별로 그룹화하여 조회
            requests = Request.objects.filter(
                customer__customer_key=customer_key
            ).select_related('design', 'shop')
            
            requests = await database_sync_to_async(list)(requests)

            # 디자인별로 요청과 응답을 그룹화
            design_requests = {}
            for request in requests:
                design_key = str(request.design.design_key)
                if design_key not in design_requests:
                    design_requests[design_key] = {
                        'design_key': design_key,
                        'design_name': request.design.design_name,
                        'shop_requests': {}
                    }

                shop_key = str(request.shop.shop_key)
                if shop_key not in design_requests[design_key]['shop_requests']:
                    design_requests[design_key]['shop_requests'][shop_key] = {
                        'shop_name': request.shop.shop_name,
                        'request_details': []
                    }

                # 해당 요청에 대한 응답들 조회
                responses = Response.objects.filter(request=request).select_related('shop')
                responses = await database_sync_to_async(list)(responses)

                # 요청과 응답을 구분하여 저장
                request_detail = {
                    'request_key': str(request.request_key),
                    'status': request.status,
                    'created_at': request.created_at.isoformat(),
                    'request': {
                        'price': request.price,  # 고객이 제시한 희망 가격
                        'contents': request.contents,  # 고객의 요청 내용
                    },
                    'response': {
                        'response_key': str(responses[0].response_key) if responses else None,
                        'price': responses[0].price if responses else None,  # 샵이 제시한 가격
                        'contents': responses[0].contents if responses else None,  # 샵의 응답 내용
                        'created_at': responses[0].created_at.isoformat() if responses else None
                    } if responses else None
                }

                design_requests[design_key]['shop_requests'][shop_key]['request_details'].append(request_detail)

            # Dictionary를 리스트로 변환하고 shop_requests도 리스트로 변환
            formatted_designs = []
            for design in design_requests.values():
                design['shop_requests'] = list(design['shop_requests'].values())
                formatted_designs.append(design)

            await self.send(text_data=json.dumps({
                "type": "response_list",
                "designs": formatted_designs
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))