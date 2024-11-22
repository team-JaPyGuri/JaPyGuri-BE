import os
import inspect
import json
import django
from typing import Dict, Any
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
        self.docs['url_pattern'] = getattr(self.consumer_class, 'url_pattern', 'ws/<path>')

        connect_method = getattr(self.consumer_class, 'connect', None)
        if connect_method:
            self.docs['connection_info'] = self._analyze_connect_method(connect_method)

        for name, method in inspect.getmembers(self.consumer_class, predicate=inspect.isfunction):
            if name.startswith('handle_'):
                self._analyze_handler_method(name, method)
            elif name.startswith('notify_'):
                self._analyze_notification_method(name, method)

        return self.docs
    
    def _analyze_connect_method(self, method) -> Dict[str, Any]:
        doc = inspect.getdoc(method) or "No description available"
        headers_section = None
        if "Headers:" in doc:
            headers_section = doc.split("Headers:")[1].strip()

        return {
            "description": doc.split("Headers:")[0].strip(),
            "headers": headers_section
        }

    def _parse_json_from_docstring(self, text: str) -> Dict:
        """Docstring에서 JSON 형식을 파싱"""
        try:
            start = text.find('{')
            if start == -1:
                return {"error": "No JSON format found"}
            
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
            json_str = json_str.replace('\n', ' ').replace('    ', ' ').strip()

            # 정리 및 변환
            json_str = json_str.replace('str', '"<string>"').replace('int', '0').replace('float', '0.0')
            json_str = json_str.replace('true', 'true').replace('false', 'false')
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON format: {e}"}
        except Exception as e:
            return {"error": str(e)}

    def _analyze_handler_method(self, name: str, method):
        doc = inspect.getdoc(method) or ""
        description = doc.split("Expected Format:")[0].strip()
        expected_format, response_format = None, None

        if "Expected Format:" in doc:
            _, formats = doc.split("Expected Format:", 1)
            if "Response Format:" in formats:
                expected_part, response_part = formats.split("Response Format:", 1)
                expected_format = self._parse_json_from_docstring(expected_part)
                response_format = self._parse_json_from_docstring(response_part)
            else:
                expected_format = self._parse_json_from_docstring(formats)
        elif "Response Format:" in doc:
            _, response_part = doc.split("Response Format:", 1)
            response_format = self._parse_json_from_docstring(response_part)

        self.docs['actions'].append({
            'name': name.replace('handle_', ''),
            'description': description,
            'expected_format': expected_format,
            'response_format': response_format
        })

    def _analyze_notification_method(self, name: str, method):
        """알림 메소드의 정보를 분석"""
        doc = inspect.getdoc(method) or "No description available"
        source = inspect.getsource(method)
        format_info = {}
        if 'json.dumps(' in source:
            try:
                source = ' '.join(line.strip() for line in source.split('\n'))
                start = source.find('json.dumps(') + len('json.dumps(')
                end = source.find(')', start)
                if start != -1 and end != -1:
                    json_str = source[start:end].strip()
                    if '{' in json_str and '}' in json_str:
                        dict_start = json_str.find('{')
                        dict_end = json_str.rfind('}') + 1
                        json_str = json_str[dict_start:dict_end]
                        json_str = json_str.replace('event["response_data"]', '{"example": "data"}')
                        json_str = json_str.replace('event["status"]', '"status"')
                        format_info = json.loads(json_str)
            except json.JSONDecodeError as e:
                format_info = {"error": f"Invalid JSON format: {e}"}
            except Exception as e:
                format_info = {"error": str(e)}

        self.docs['notifications'].append({
            'name': name.replace('notify_', ''),
            'description': doc.split('\n')[0],
            'format': format_info
        })


    def generate_markdown(self) -> str:
        md_content = f"""## WebSocket API Documentation

### Connection URL Pattern
{self.docs['url_pattern']}

### Connection Information
{self.docs['connection_info'].get('description', '')}
{self.docs['connection_info'].get('headers', '')}

### Available Actions
"""
        for action in self.docs['actions']:
            md_content += f"\n#### {action['name']}\n{action['description']}\n\n"
            if action.get('expected_format'):
                md_content += f"Expected Format:\n```json\n{json.dumps(action['expected_format'], indent=2)}\n```\n"
            if action.get('response_format'):
                md_content += f"Response Format:\n```json\n{json.dumps(action['response_format'], indent=2)}\n```\n"

        if self.docs['notifications']:
            md_content += "\n### Notifications\n"
            for notification in self.docs['notifications']:
                md_content += f"\n#### {notification['name']}\n{notification['description']}\n"
                if notification.get('format'):
                    md_content += f"Format:\n```json\n{json.dumps(notification['format'], indent=2)}\n```\n"

        return md_content

    def update_readme(self, readme_path: str = "README.md"):
        """README.md 파일을 생성하거나 기존 내용을 새로 씁니다."""
        readme_path = Path(readme_path)
        
        # WebSocket API 문서 생성
        websocket_docs = self.generate_markdown()

        # README.md 내용을 새로 작성
        new_content = "# Project Name\n\n" + websocket_docs

        # 파일에 새로 작성
        readme_path.write_text(new_content, encoding='utf-8')
        print(f"Generated new README.md with WebSocket API documentation at {readme_path}")


if __name__ == "__main__":
    doc_generator = WebSocketDocGenerator(NailServiceConsumer)
    doc_generator.analyze_consumer()
    doc_generator.update_readme("README.md")

