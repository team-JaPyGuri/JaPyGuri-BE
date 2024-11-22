import os
import sys
import django
from django.conf import settings
from django.core.management import call_command
from django.apps import apps
from decimal import Decimal
from decouple import config
from django.db import connections

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_connections():
    """현재 데이터베이스 연결 상태를 출력합니다."""
    print("\n현재 데이터베이스 연결 상태:")
    for db_alias in settings.DATABASES.keys():
        print(f"- {db_alias}: {settings.DATABASES[db_alias]['ENGINE']} ({settings.DATABASES[db_alias]['NAME']})")

def setup_databases():
    """MySQL과 SQLite 데이터베이스 설정을 수정합니다."""
    # 기존 연결 닫기
    connections.close_all()
    
    # 기존 MySQL 설정 백업
    mysql_settings = settings.DATABASES['default'].copy()
    
    # SQLite 설정
    sqlite_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
        print("기존 SQLite 데이터베이스를 삭제했습니다.")
    
    # 데이터베이스 설정 수정
    settings.DATABASES = {
        'source': mysql_settings,  # MySQL 설정
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }
    }
    
    debug_connections()
    return mysql_settings

def migrate_data():
    """데이터를 MySQL에서 SQLite로 마이그레이션합니다."""
    try:
        print("1. SQLite 데이터베이스 스키마 생성 중...")
        call_command('migrate', verbosity=1)
        
        print("\n2. 데이터 마이그레이션 시작...")
        
        # 연결 확인
        from django.db import connections
        if 'source' not in connections.databases:
            raise Exception("Source database connection not configured")
        
        models_order = [
            'Shops',
            'Customers',
            'Designs',
            'Like',
            'Request',
            'Response'
        ]
        
        for model_name in models_order:
            model = apps.get_model('nailo_be', model_name)
            print(f"\n{model_name} 마이그레이션 중...")
            
            try:
                print(f"source 데이터베이스에서 {model_name} 데이터를 가져오는 중...")
                # 데이터 가져오기 전에 connection 확인
                with connections['source'].cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM nailo_be_{model_name.lower()}")
                    count = cursor.fetchone()[0]
                    print(f"- 테이블에서 {count}개의 레코드 확인됨")
                
                # MySQL에서 데이터 가져오기
                objects = list(model.objects.using('source').all())
                total_count = len(objects)
                
                if total_count == 0:
                    print(f"- {model_name}에 데이터가 없습니다.")
                    continue
                
                print(f"- 총 {total_count}개의 레코드 처리 중...")
                
                # 배치 처리
                batch_size = 1000
                for i in range(0, total_count, batch_size):
                    batch = objects[i:i + batch_size]
                    
                    # Shops 모델의 DecimalField 처리
                    if model_name == 'Shops':
                        for obj in batch:
                            obj.lat = Decimal(str(obj.lat))
                            obj.lng = Decimal(str(obj.lng))
                    
                    # SQLite로 데이터 저장
                    for obj in batch:
                        # UUID 필드 보존
                        original_pk = obj.pk
                        new_obj = model()
                        
                        # 모든 필드 복사
                        for field in model._meta.fields:
                            if field.primary_key:
                                setattr(new_obj, field.name, original_pk)
                            else:
                                setattr(new_obj, field.name, getattr(obj, field.name))
                        
                        new_obj.save(using='default')
                    
                    print(f"- {i + len(batch)}/{total_count} 레코드 완료")
                
                print(f"{model_name} 마이그레이션 완료!")
                
            except Exception as e:
                print(f"{model_name} 처리 중 오류 발생: {str(e)}")
                raise

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        raise

def main():
    """메인 마이그레이션 프로세스"""
    original_settings = None
    
    try:
        print("마이그레이션 시작...")
        print(f"현재 데이터베이스: {settings.DATABASES['default']['NAME']}")
        
        # 데이터베이스 설정 변경
        original_settings = setup_databases()
        
        # 데이터 마이그레이션 실행
        migrate_data()
        
        print("\n마이그레이션이 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"\n마이그레이션 실패: {str(e)}")
        print("원래 데이터베이스는 영향받지 않았습니다.")
        
    finally:
        if original_settings:
            # 원래 설정으로 복원
            settings.DATABASES['default'] = original_settings
            if 'source' in settings.DATABASES:
                del settings.DATABASES['source']

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nailo.settings')
    django.setup()
    
    main()