# Project Name

## WebSocket API Documentation

### Connection URL Pattern
ws/<user_type>/<user_id>

### Connection Information
WebSocket 연결을 처리합니다.
- x-user-type: "customer" | "shop"
- x-user-id: str

### Available Actions

#### nearby_shops
주변 네일샵 정보를 조회합니다.

Response Format:
```json
{
  "type": "shop_list",
  "shops": [
    {
      "shop_key": "<uuid>",
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
    "customer_key": "<uuid>",
    "design_key": "<uuid>",
    "shop_key": "<uuid>",
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
  "action": "respond_service",
  "data": {
    "request_key": "<uuid>",
    "status": "accepted | rejected",
    "price": "<int>",
    "contents": "<string>"
  }
}
```
Response Format:
```json
{
  "type": "completed_response",
  "status": "<string>",
  "response_data": {
    "shop_name": "<string>",
    "price": "<int>",
    "contents": "<string>"
  }
}
```
#### get_responses
고객 화면에서 디자인별 응답 목록을 조회합니다.

Expected Format:
```json
{
    "action": "get_responses",
    "data":{
        "customer_key": "<uuid>",
    }
}
```

Response Format:
```json
{
  "type": "response_list",
  "designs": [
    {
      "design_key": "<uuid>",
      "design_name": "<string>",
      "shop_requests": [
        {
          "shop_name": "<string>",
          "request_details": [
            {
              "request_key": "<uuid>",
              "status": "accepted | rejected",
              "created_at": "<DATETIME>",
              "request": {
                "price": "<int>",
                "contents": "<string>"
              },
              "response": {
                "response_key": "<uuid>",
                "price": "<int>",
                "contents": "<string>",
                "created_at": "<DATETIME>"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### get_requests
샵 화면에서 고객의 요청 목록을 조회합니다.

Expected Format:
```json
{
    "action": "get_requests",
    "data": {
        "shop_key": "<uuid>"
    }
}
```

Response Format:
```json
{
    "type": "request_list",
    "requests": [
        {
            "request_key": "<uuid>",
            "customer_name": "<string>",
            "design_name": "<string>",
            "status": "<string>",
            "created_at": "<DATETIME>",
            "price": "<int>",
            "contents": "<string>"
        }
    ]
}
```

### Notifications

#### customer_new_response
샵의 응답이 도착했음을 고객에게 알림
Format:
```json
{
  "type": "new_response",
  "shop_name": "<string>",
  "request_key": "<string>"
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
  "request_key": "<string>"
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
