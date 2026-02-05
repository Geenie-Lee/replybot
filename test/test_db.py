
import sys
import os

# 현재 디렉토리의 부모 디렉토리를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from db_logger import DBLogger
import tomllib

print("🔍 DB 연결 및 테이블 생성 테스트 시작")

# 1. config.toml 확인 (부모 디렉토리)
config_path = os.path.join(parent_dir, 'config/config.toml')
print(f"📂 설정 파일 경로: {config_path}")

if os.path.exists(config_path):
    print("✅ config.toml 파일 존재함")
    with open(config_path, 'rb') as f:
        try:
            config = tomllib.load(f)
            print(f"📊 설정 로드 내용 (database): {config.get('database')}")
        except Exception as e:
            print(f"❌ 설정 파일 파싱 실패: {e}")
else:
    print("❌ config.toml 파일이 없음!")

# 2. DBLogger 인스턴스 생성 (이때 테이블 생성 시도함)
try:
    logger = DBLogger(config_path=config_path)
    print("✅ DBLogger 인스턴스 생성 완료")
except Exception as e:
    print(f"❌ DBLogger 생성 실패: {e}")
    sys.exit(1)

# 3. 테스트 로그 적재
try:
    print("📝 테스트 로그 적재 시도...")
    logger.log_query(
        customer_number="TEST_USER",
        consultation_type="TEST_TYPE",
        query_text="테스트 쿼리입니다.",
        predicted_template_id=999,
        confidence=0.99,
        processing_time=0.123,
        client_ip="127.0.0.1"
    )
    print("✅ 테스트 로그 적재 성공")
except Exception as e:
    print(f"❌ 테스트 로그 적재 실패: {e}")
