# JaPyGuri-BE
## WebSocket API Documentation

### Connection URL Pattern
```
ws/<path>
```

### Connection Information
WebSocket 연결을 처리합니다.

- x-user-type: "customer" | "shop"
- x-user-id: str

### Available Actions

#### get_responses
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

Response Format:
```json
{
  "type": "response_list",
  "designs": [
    {
      "design_key": "<string>",
      "design_name": "<string>",
      "shop_requests": [
        {
          "shop_name": "<string>",
          "request_details": [
            {
              "request_key": "<string>",
              "status": "<string>",
              "created_at": "<string>",
              "request": {
                "price": 0,
                "contents": "<string>"
              },
              "response": {
                "response_key": "<string>",
                "price": 0,
                "contents": "<string>",
                "created_at": "<string>"
              }
            }
          ]
        }
      ]
    }
  ]
}
```


#### nearby_shops
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

Response Format:
```json
{
  "type": "shop_list",
  "shops": [
    {
      "shop_key": "<string>",
      "shop_name": "<string>",
      "shop_id": "<string>",
      "lat": 0.0,
      "lng": 0.0,
      "shop_url": "<string>"
    }
  ]
}
```


#### service_request
시술 요청을 처리합니다.

Expected Format:
```json
{
  "action": "request_service",
  "data": {
    "customer_key": "<string>",
    "design_key": "<string>",
    "shop_key": "<string>",
    "contents": "<string>"
  }
}
```

Response Format:
```json
{
  "type": "completed_request",
  "status": "pending",
  "message": "<string>"
}
```


#### service_response
시술 요청에 대한 응답을 처리합니다.

Expected Format:
```json
{
  "error": "Invalid JSON format"
}
```

Response Format:
```json
{
  "type": "completed_response",
  "status": "<string>",
  "response_data": {
    "shop_name": "<string>",
    "price": 0,
    "contents": "<string>"
  }
}
```


### Notifications

#### customer_new_response
샵의 응답이 도착했음을 고객에게 알림

Format:
```json
{
  "type": "new_response",
  "shop_name": "Shop Name",
  "request_key": "request-123"
}
```

#### customer_request_sent
고객의 요청이 정상적으로 전송되었음을 고객에게 알림

Format:
```json
{
  "type": "completed_request",
  "status": "pending",
  "request_data": {
    "example": "data"
  }
}
```

#### shop_new_request
고객의 요청이 도착했음을 샵에게 알림

Format:
```json
{
  "type": "new_request",
  "request_key": "request-123"
}
```

#### shop_response_sent
샵의 응답이 정상적으로 전송되었음을 샵에게 알림

Format:
```json
{
  "type": "completed_response",
  "status": "status",
  "response_data": {
    "example": "data"
  }
}
```
