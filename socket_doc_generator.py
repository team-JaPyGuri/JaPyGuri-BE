import os
import inspect
import json
from typing import Dict, Any, Optional
from pathlib import Path


class WebSocketDocGenerator:
    def __init__(self, consumer_class):
        self.consumer_class = consumer_class
        self.docs = {
            'url_pattern': '',
            'connection_info': {},
            'actions': [],
            'notifications': []
        }

    def analyze_consumer(self) -> Dict[str, Any]:
        """Consumer 클래스를 분석하여 문서화할 정보를 수집합니다."""
        self.docs['url_pattern'] = 'ws/<user_type>/<user_id>'

        connect_method = getattr(self.consumer_class, 'connect', None)
        if connect_method:
            self.docs['connection_info'] = self._analyze_connect_method(connect_method)

        # 핸들러와 알림 메소드 분석
        for name, method in inspect.getmembers(self.consumer_class, predicate=inspect.isfunction):
            if name.startswith('handle_'):
                self._analyze_handler_method(name, method)
            elif name.startswith('notify_'):
                self._analyze_notification_method(name, method)

        return self.docs
    
    def _analyze_connect_method(self, method) -> Dict[str, Any]:
        """연결 메소드의 정보를 분석합니다."""
        doc = inspect.getdoc(method) or "No description available"
        
        # Headers 섹션 추출
        headers_info = ""
        if "Headers:" in doc:
            headers_section = doc.split("Headers:")[1].strip()
            headers_info = f"\nHeaders:\n{headers_section}"

        return {
            "description": doc.split("Headers:")[0].strip(),
            "headers": headers_info
        }
        
    def _format_json(self, data: Dict) -> str:
        """JSON을 보기 좋게 포맷팅합니다."""
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _clean_json_str(self, json_str: str) -> str:
        """JSON 문자열을 정리합니다."""
        return (json_str
            .replace('\\', '')  # escape 문자 제거
            .replace('""', '"')  # 중복 따옴표 정리
            .replace('str', '"string"')
            .replace('int', '0')
            .replace('float', '0.0')
            .replace('bool', 'true')
            .replace('Dict[str, Any]', '{}')
            .replace('List[str]', '[]'))

    def _analyze_handler_method(self, name: str, method):
        """핸들러 메소드의 정보를 분석합니다."""
        doc = inspect.getdoc(method) or ""
        description = doc.split("Expected Format:")[0].strip() if "Expected Format:" in doc else doc

        expected_format = None
        response_format = None

        # Expected Format 파싱
        if "Expected Format:" in doc:
            expected_text = doc.split("Expected Format:")[1]
            if "Response Format:" in expected_text:
                expected_text = expected_text.split("Response Format:")[0]
            expected_format = self._parse_json_from_docstring(expected_text)

        # Response Format 파싱
        if "Response Format:" in doc:
            response_text = doc.split("Response Format:")[1]
            response_format = self._parse_json_from_docstring(response_text)

        self.docs['actions'].append({
            'name': name.replace('handle_', ''),
            'description': description,
            'expected_format': expected_format,
            'response_format': response_format
        })
        
    def _analyze_notification_method(self, name: str, method):
        """알림 메소드의 정보를 분석합니다."""
        doc = inspect.getdoc(method) or "No description available"
        source = inspect.getsource(method)
        
        # 실제 notification 포맷 추출
        format_info = {}
        notification_type = name.replace('notify_', '')
        
        if notification_type == 'customer_new_response':
            format_info = {
                "type": "new_response",
                "shop_name": "string",
                "request_key": "string"
            }
        elif notification_type == 'shop_new_request':
            format_info = {
                "type": "new_request",
                "request_key": "string"
            }
        elif notification_type == 'customer_request_sent':
            format_info = {
                "type": "completed_request",
                "status": "pending",
                "request_data": {"example": "data"}
            }
        elif notification_type == 'shop_response_sent':
            format_info = {
                "type": "completed_response",
                "status": "string",
                "response_data": {
                    "shop_name": "string",
                    "price": 0,
                    "contents": "string"
                }
            }

        self.docs['notifications'].append({
            'name': notification_type,
            'description': doc,
            'format': format_info
        })

    def _parse_json_from_docstring(self, text: str) -> Optional[Dict]:
        """Docstring에서 JSON 형식을 추출하고 파싱합니다."""
        try:
            # 여러 줄의 텍스트에서 JSON 부분 추출
            lines = text.strip().split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                if '{' in line:
                    in_json = True
                if in_json:
                    json_lines.append(line)
                if '}' in line:
                    break
                    
            if json_lines:
                json_str = ' '.join(json_lines)
                json_str = self._clean_json_str(json_str)
                return json.loads(json_str)
            
            return None
        except Exception:
            return None

    def generate_markdown(self) -> str:
        """마크다운 형식의 문서를 생성합니다."""
        md_content = f"""# WebSocket API Documentation

## Connection Information
### URL Pattern
{self.docs['url_pattern']}

### Description
{self.docs['connection_info'].get('description', '')}
{self.docs['connection_info'].get('headers', '')}

## Available Actions
"""
        # Actions 섹션
        for action in self.docs['actions']:
            md_content += f"\n### {action['name']}\n{action['description']}\n\n"
            
            if action.get('expected_format'):
                md_content += "**Expected Format:**\n```json\n"
                md_content += self._format_json(action['expected_format'])
                md_content += "\n```\n\n"
            
            if action.get('response_format'):
                md_content += "**Response Format:**\n```json\n"
                md_content += self._format_json(action['response_format'])
                md_content += "\n```\n\n"

        # Notifications 섹션
        if self.docs['notifications']:
            md_content += "\n## Notifications\n"
            for notification in self.docs['notifications']:
                md_content += f"\n### {notification['name']}\n{notification['description']}\n\n"
                if notification.get('format'):
                    md_content += "**Format:**\n```json\n"
                    md_content += self._format_json(notification['format'])
                    md_content += "\n```\n\n"

        return md_content

    def generate_docs(self, output_path: str = "websocket_api_docs.md"):
        """WebSocket API 문서를 생성합니다."""
        self.analyze_consumer()
        docs_content = self.generate_markdown()
        
        output_path = Path(output_path)
        output_path.write_text(docs_content, encoding='utf-8')
        print(f"Generated WebSocket API documentation at {output_path}")


if __name__ == "__main__":
    # Django 설정이 필요한 경우 아래 코드 추가
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")
    django.setup()

    from nailo_be.consumers import NailServiceConsumer
    
    doc_generator = WebSocketDocGenerator(NailServiceConsumer)
    doc_generator.generate_docs("websocket_api_docs.md")