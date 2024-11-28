import json
import logging
from typing import Dict, Any
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from .models import Request, Response, Designs, Shops, Customers
from .serializers import RequestSerializer, ResponseSerializer, AddRequestSerializer, ResponseListSerializer
from .utils import get_user_id

logger = logging.getLogger('nailo_be.consumers')

class NailServiceConsumer(AsyncWebsocketConsumer):

    """네일 서비스 WebSocket Consumer"""
    
    async def connect(self) -> None:
        """
        WebSocket 연결을 처리합니다.
        
        Headers:
        - x-user-type: "customer" | "shop"
        - x-user-id: str
        """
        try:
            self.user_type = self.scope['url_route']['kwargs']['user_type']
            self.user_id = self.scope['url_route']['kwargs']['user_id']
            
            logger.info(f"Connection attempt: user_type={self.user_type}, user_id={self.user_id}")
            
            # 그룹 이름 설정
            self.group_name = f"{self.user_type}_{self.user_id}"
            
            # 사용자 객체 가져오기
            user, user_type = await database_sync_to_async(get_user_id)(self.user_type, self.user_id)
            self.user = user
            self.user_type = user_type
            
            # 고객 또는 샵의 key값 가져오기
            if self.user_type == "customer":
                self.customer_key = self.user.customer_key    
            elif self.user_type == "shop":          
                self.shop_key = self.user.shop_key            
                
            # 그룹에 추가
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

            # 연결 성공 시 프론트에 알림
            if self.user_type == "customer":
                await self.send(text_data=json.dumps({
                    "message": f"Connected as customer: {self.user}, key={self.customer_key}"
                }, ensure_ascii=False))
                logger.info(f"Connected to customer: {self.user}, key={self.customer_key}")
            
            elif self.user_type == "shop":
                await self.send(text_data=json.dumps({
                    "message": f"Connected as shop: {self.user}, key={self.shop_key}"
                }, ensure_ascii=False))
                logger.info(f"Connected to shop: {self.user}, key={self.shop_key}")
        
        except ValueError as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close()
        
        except Exception as e:
            logger.error(f"Unexpected error during WebSocket connection: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        """WebSocket 연결 종료를 처리합니다."""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket connection closed for {self.user_type}: {self.user.customer_id if self.user_type == 'customer' else self.user.shop_id}")

    async def receive(self, text_data: str) -> None:
        """
        클라이언트로부터 WebSocket 메시지를 수신하고 처리합니다.
        
        Expected Format:
        {
            "action": str,  # "nearby_shops" | "request_service" | "respond_service" | "get_responses"
            ... action별 추가 데이터
        }
        """
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
            elif action == "get_requests": 
                await self.handle_get_requests(data)
            if action == "try_on":
                await self.handle_try_on(data)
            else:
                await self.send(text_data=json.dumps({
                    "error": f"Unknown action: {action}"
                }, ensure_ascii=False))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON format"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))

    async def handle_nearby_shops(self, data: Dict[str, Any]) -> None:
        """
        주변 네일샵 정보를 조회합니다.
        
        Response Format:
        {
            "type": "shop_list",
            "shops": [
                {
                    "shop_key": str,
                    "shop_name": str,
                    "shop_id": str,
                    "lat": float,
                    "lng": float,
                    "shop_url": str
                }
            ]
        }
        """
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

            print("Processed shops data:", shops)
            
            await self.send(text_data=json.dumps({
                "type": "shop_list",
                "shops": shops
            }, ensure_ascii=False))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))
        
    async def handle_service_request(self, data: Dict[str, Any]) -> None:
        """
        시술 요청을 처리합니다.
        
        Expected Format:
        {
            "action": "request_service",
            "data": {
                "customer_key": str,
                "design_key": str,
                "shop_key": str,
                "contents": str
            }
        }
        
        Response Format:
        {
            "type": "completed_request",
            "status": "pending",
            "message": str
        }
        """
        try:
            serializer = RequestSerializer(data=data.get('data', {}))
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
            shop = await database_sync_to_async(Shops.objects.get)(
                shop_key=serializer.validated_data['shop_key']
            )

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
            }, ensure_ascii=False))

        except (Customers.DoesNotExist, Designs.DoesNotExist) as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))
        
        except Shops.DoesNotExist:
            await self.send(text_data=json.dumps({
                "error": "Invalid shop_key: Shop not found"
            }, ensure_ascii=False))
            return
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))

    async def handle_service_response(self, data: Dict[str, Any]) -> None:
        """
        시술 요청에 대한 응답을 처리합니다.
        
        Expected Format:
        {
            "action": "respond_service",
            "data":{
                "request_key": str,
                "status": "accepted" | "rejected",
                "price": int,
                "contents": str
            }
        }
        
        Response Format:
        {
            "type": "completed_response",
            "status": str,
            "response_data": {
                "shop_name": str,
                "price": int,
                "contents": str
            }
        }
        """
        try:
            data = data.get('data', {})
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
                }, ensure_ascii=False))
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
            }, ensure_ascii=False))

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
            
    async def notify_customer_request_sent(self, event: Dict[str, Any]) -> None:
        """고객의 요청이 정상적으로 전송되었음을 고객에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "completed_request",
            "status": "pending",
            "request_data": event["response_data"]
        }, ensure_ascii=False))

    async def notify_shop_response_sent(self, event: Dict[str, Any]) -> None:
        """샵의 응답이 정상적으로 전송되었음을 샵에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "completed_response",
            "status": event["status"],
            "response_data": event["response_data"]
        }, ensure_ascii=False))

    async def notify_shop_new_request(self, event: Dict[str, Any]) -> None:
        """고객의 요청이 도착했음을 샵에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "new_request",
            "request_key": event["request_key"]
        }, ensure_ascii=False))

    async def notify_customer_new_response(self, event: Dict[str, Any]) -> None:
        """샵의 응답이 도착했음을 고객에게 알림"""
        await self.send(text_data=json.dumps({
            "type": "new_response",
            "shop_name": event["shop_name"],
            "request_key": event["request_key"]
        }, ensure_ascii=False))
        
    async def handle_get_responses(self, data: Dict[str, Any]) -> None:
        """
        디자인별 응답 목록을 조회합니다.
        
        {
            "action": "get_responses"
            "data":{
                "customer_key": str
            }
        }
        Response Format:
        {
            "type": "response_list",
            "designs": [
                {
                    "design_key": str,
                    "design_name": str,
                    "shop_requests": [
                        {
                            "shop_name": str,
                            "request_details": [
                                {
                                    "request_key": str,
                                    "status": str,
                                    "created_at": str,
                                    "request": {
                                        "price": int,
                                        "contents": str
                                    },
                                    "response": {
                                        "response_key": str,
                                        "price": int,
                                        "contents": str,
                                        "created_at": str
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        """
        try:
            customer_key = data.get('data', {}).get('customer_key')
            if not customer_key:
                await self.send(text_data=json.dumps({
                    "error": "customer key is required"
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
            }, ensure_ascii=False))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))
    
    async def handle_get_requests(self, data: Dict[str, Any]) -> None:
        """
        샵 화면에서 고객의 요청 목록을 조회합니다.

        {
            "action": "get_requests",
            "data": {
                "shop_key": str
            }
        }
        
        Response Format:
        {
            "type": "request_list",
            "requests": [
                {
                    "request_key": str,
                    "customer_name": str,
                    "design_name": str,
                    "status": str,
                    "created_at": str,
                    "price": int,
                    "contents": str
                }
            ]
        }
        """
        try:
            shop_key = data.get('data', {}).get('shop_key')
            if not shop_key:
                await self.send(text_data=json.dumps({
                    "error": "shop key is required"
                }))
                return

            requests = Request.objects.filter(
                shop__shop_key=shop_key
            ).select_related('customer', 'design')
            
            requests = await database_sync_to_async(list)(requests)

            formatted_requests = []
            for request in requests:
                formatted_requests.append({
                    "request_key": str(request.request_key),
                    "customer_name": request.customer.customer_name,
                    "design_name": request.design.design_name,
                    "status": request.status,
                    "created_at": request.created_at.isoformat(),
                    "price": request.price,
                    "contents": request.contents
                })

            await self.send(text_data=json.dumps({
                "type": "request_list",
                "requests": formatted_requests
            }, ensure_ascii=False))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))
    
    async def notify_tryon_result(self, event):
        """
        WebSocket 그룹에 Try-On 결과 알림을 전송합니다.
        """
        await self.send(
            text_data=json.dumps({
                "type": "tryon_result",
                "message": "이미지가 생성되었습니다.",
                # "original_image": event["original_image"],
                # "predicted_image": event["predicted_image"]
            }, ensure_ascii=False)
        )
