import os
import inspect
import json
import django
from typing import Type, Dict, Any, List
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nailo.settings")
django.setup()

from nailo_be.consumers import NailServiceConsumer

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
        """Consumer 클래스를 분석하여 문서화할 정보를 추출합니다."""
        # URL 패턴 추출
        self.docs['url_pattern'] = getattr(self.consumer_class, 'url_pattern', 'ws/<path>')
        
        # Connect 메소드 분석
        connect_method = getattr(self.consumer_class, 'connect', None)
        if connect_method:
            self.docs['connection_info'] = self._analyze_connect_method(connect_method)

        # 핸들러 메소드 분석
        for name, method in inspect.getmembers(self.consumer_class, predicate=inspect.isfunction):
            if name.startswith('handle_'):
                self._analyze_handler_method(name, method)
            elif name.startswith('notify_'):
                self._analyze_notification_method(name, method)

        return self.docs
    
    def _analyze_connect_method(self, method) -> Dict[str, Any]:
        """연결 메소드의 정보를 분석합니다."""
        doc = inspect.getdoc(method)
        if not doc:
            return {"description": "No description available"}

        # docstring에서 헤더 정보 추출
        headers_section = None
        if "Headers:" in doc:
            headers_section = doc.split("Headers:")[1].strip()

        return {
            "description": doc.split("Headers:")[0].strip() if headers_section else doc,
            "headers": headers_section
        }

    def _parse_json_from_docstring(self, text: str) -> Dict:
        """docstring에서 JSON 형식을 파싱합니다."""
        try:
            # 중괄호로 시작하는 부분을 찾아서 파싱
            start = text.find('{')
            if start == -1:
                return {"error": "No JSON format found"}
            
            # 균형잡힌 중괄호 찾기
            count = 0
            end = start
            for i in range(start, len(text)):
                if text[i] == '{':
                    count += 1
                elif text[i] == '}':
                    count -= 1
                if count == 0:
                    end = i + 1
                    break
            
            json_str = text[start:end]
            # 줄바꿈과 공백 정리
            json_str = json_str.replace('\n', ' ').replace('    ', ' ').strip()
            
            # Union 타입("accepted" | "rejected" 같은 형식) 처리
            import re
            union_pattern = r'"([^"]+)"\s*\|\s*"([^"]+)"'
            json_str = re.sub(union_pattern, r'"\1"', json_str)
            
            # 타입 표시를 실제 값으로 변환
            json_str = json_str.replace('str', '"<string>"')
            json_str = json_str.replace('int', '0')
            json_str = json_str.replace('float', '0.0')
            json_str = json_str.replace('bool', 'true')
            json_str = json_str.replace(': "accepted"', ': "<accepted or rejected>"')
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format"}
        except Exception as e:
            return {"error": str(e)}

    def _analyze_handler_method(self, name: str, method):
        """핸들러 메소드의 정보를 분석합니다."""
        doc = inspect.getdoc(method)
        if not doc:
            return

        description = doc
        expected_format = None
        response_format = None

        if "Expected Format:" in doc:
            description, format_part = doc.split("Expected Format:", 1)
            if "Response Format:" in format_part:
                expected_part, response_part = format_part.split("Response Format:", 1)
                expected_format = self._parse_json_from_docstring(expected_part)
                response_format = self._parse_json_from_docstring(response_part)
            else:
                expected_format = self._parse_json_from_docstring(format_part)
        
        # Response Format만 있는 경우
        elif "Response Format:" in doc:
            description, response_part = doc.split("Response Format:", 1)
            response_format = self._parse_json_from_docstring(response_part)
            
        action_info = {
            'name': name.replace('handle_', ''),
            'description': doc.split("Expected Format:")[0].strip() if "Expected Format:" in doc else doc,
            'expected_format': expected_format,
            'response_format': response_format
        }
        
        self.docs['actions'].append(action_info)

    def _analyze_notification_method(self, name: str, method):
        """알림 메소드의 정보를 분석합니다."""
        doc = inspect.getdoc(method)
        source = inspect.getsource(method)
        
        # 메소드 내의 json.dumps 호출에서 직접 포맷 추출
        format_info = {}
        if 'json.dumps(' in source:
            try:
                # 여러 줄의 소스 코드를 한 줄로
                source = ' '.join(line.strip() for line in source.split('\n'))
                start = source.find('json.dumps(') + len('json.dumps(')
                end = source.find(')', start)
                if start != -1 and end != -1:
                    json_str = source[start:end].strip()
                    # 소스 코드에서 실제 딕셔너리 부분만 추출
                    if '{' in json_str and '}' in json_str:
                        dict_start = json_str.find('{')
                        dict_end = json_str.rfind('}') + 1
                        json_str = json_str[dict_start:dict_end]
                        # 변수 참조를 실제 값으로 변환
                        json_str = json_str.replace('event["response_data"]', '{"example": "data"}')
                        json_str = json_str.replace('event["status"]', '"status"')
                        json_str = json_str.replace('event["request_key"]', '"request-123"')
                        json_str = json_str.replace('event["shop_name"]', '"Shop Name"')
                        format_info = json.loads(json_str)
            except:
                pass

        notification_info = {
            'name': name.replace('notify_', ''),
            'description': doc.split('\n')[0] if doc else "No description available",
            'format': format_info
        }
        self.docs['notifications'].append(notification_info)

    def generate_markdown(self) -> str:
        """웹소켓 API 문서를 Markdown 형식으로 생성합니다."""
        md_content = f"""## WebSocket API Documentation

### Connection URL Pattern
```
{self.docs['url_pattern']}
```

### Connection Information
{self.docs['connection_info'].get('description', '')}

{self.docs['connection_info'].get('headers', '')}

### Available Actions
"""
        # Actions 문서화
        for action in self.docs['actions']:
            md_content += f"\n#### {action['name']}\n"
            md_content += f"{action['description']}\n\n"
            
            if action.get('expected_format'):
                md_content += "Expected Format:\n```json\n"
                md_content += json.dumps(action['expected_format'], indent=2)
                md_content += "\n```\n\n"
            
            if 'response_format' in action:  # response_format이 None이어도 처리
                md_content += "Response Format:\n```json\n"
                if isinstance(action['response_format'], (dict, list)):
                    md_content += json.dumps(action['response_format'], indent=2)
                else:
                    md_content += str(action['response_format']).strip()
                md_content += "\n```\n\n"
                
        # Notifications 문서화
        if self.docs['notifications']:
            md_content += "\n### Notifications\n"
            for notification in self.docs['notifications']:
                md_content += f"\n#### {notification['name']}\n"
                md_content += f"{notification['description']}\n\n"
                if notification.get('format'):
                    md_content += "Format:\n```json\n"
                    md_content += json.dumps(notification['format'], indent=2)
                    md_content += "\n```\n"

        return md_content

    def update_readme(self, readme_path: str = "README.md"):
        """README.md 파일을 업데이트합니다."""
        readme_path = Path(readme_path)
        
        if not readme_path.exists():
            print(f"Creating new README.md file at {readme_path}")
            readme_content = "# Project Name\n\n"
        else:
            readme_content = readme_path.read_text(encoding='utf-8')

        websocket_docs = self.generate_markdown()
        
        if "## WebSocket API Documentation" in readme_content:
            parts = readme_content.split("## WebSocket API Documentation")
            before_docs = parts[0]
            after_docs = ""
            if len(parts) > 1:
                next_section_match = parts[1].find("\n## ")
                if next_section_match != -1:
                    after_docs = parts[1][next_section_match:]
            new_content = before_docs + websocket_docs + after_docs
        else:
            new_content = readme_content + "\n" + websocket_docs

        readme_path.write_text(new_content, encoding='utf-8')
        print(f"Updated WebSocket API documentation in {readme_path}")

if __name__ == "__main__":
    doc_generator = WebSocketDocGenerator(NailServiceConsumer)
    doc_generator.analyze_consumer()
    doc_generator.update_readme("README.md")