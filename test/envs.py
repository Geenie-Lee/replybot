import os
import socket
import json
import pickle
import datetime

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def get_file_metadata(filepath):
    if not os.path.exists(filepath):
        return None
    stat = os.stat(filepath)
    return {
        'size': format_size(stat.st_size),
        'modified': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title} ".center(60, '*'))
    print(f"{'='*60}")

def check_env():
    # 1. Load config
    config_path = 'config/config.toml'
    if not os.path.exists(config_path):
        print(f"❌ config.toml을 [{config_path}]에서 찾을 수 없습니다.")
        return

    try:
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
    except Exception as e:
        print(f"❌ TOML 파싱 에러: {e}")
        return

    # 2. Database Check
    print_section("Database Environment")
    db_config = config.get('database', {})
    if not db_config:
        print("⚠️ 설정 항목 [database]가 없습니다.")
    else:
        host = db_config.get('host')
        port = db_config.get('port')
        user = db_config.get('user')
        password = db_config.get('password')
        dbname = db_config.get('database')
        
        print(f"📄 DB 접속 정보:")
        print(f"   - Host    : {host}")
        print(f"   - Port    : {port}")
        print(f"   - DB Name : {dbname}")
        print(f"   - User    : {user}")
        
        print(f"\n🔌 접속 테스트 시도 중...")
        try:
            from sqlalchemy import create_engine, text
            db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
            engine = create_engine(db_uri, pool_pre_ping=True, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                res = conn.execute(text("SELECT VERSION()")).scalar()
                print(f"   ✅ 접속 성공! (MySQL Version: {res})")
        except ImportError:
             print("   ⚠️ sqlalchemy 또는 mysqlconnector 모듈이 설치되어 있지 않아 접속 점검은 건너뜁니다.")
        except Exception as e:
            print(f"   ❌ 접속 실패: 기동되어 있지 않거나, 정보가 올바르지 않습니다.")
            print(f"      (상세에러: {e})".split('\n')[0])

    # 3. Server Check
    print_section("Server Configuration")
    server_config = config.get('server', {})
    if not server_config:
         print("⚠️ 설정 항목 [server]가 없습니다.")
    else:
        server_port = server_config.get('port', 5000)
        print(f"📄 설정 정보:")
        for k, v in server_config.items():
            if 'secret' in k or 'password' in k:
                v = '*' * len(str(v)) if v else v
            print(f"   - {k:<15}: {v}")

        print(f"\n📡 포트 상태 점검 중 (Port {server_port})...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', int(server_port)))
        if result == 0:
            print(f"   ✅ 포트 {server_port}는 로컬에서 현재 열려(사용 중) 있습니다.")
        else:
            print(f"   ⚪ 포트 {server_port}는 현재 닫혀 있습니다. (서버 미실행 상태)")
        sock.close()

    # 4. Files Check
    print_section("Files & Models Metadata")
    files_config = config.get('files', {})
    
    # Model PKL check
    model_path = files_config.get('model', 'model/randomforest_model.pkl')
    print(f"🧠 [모델 정보] 경로: {model_path}")
    meta = get_file_metadata(model_path)
    if not meta:
        print(f"   ❌ 파일을 찾을 수 없습니다.")
    else:
        print(f"   ✅ 크기: {meta['size']} | 수정일: {meta['modified']}")
        
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            print(f"   🔍 세부 정보 분석 중...")
            if isinstance(model_data, dict):
                model_obj = model_data.get('model')
                if model_obj:
                    print(f"      - 모델 타입      : {type(model_obj).__name__}")
                    if hasattr(model_obj, 'classes_'):
                         print(f"      - 대상 클래스 수 : {len(model_obj.classes_)} Classes")
                else:
                    print("      - 사전(Dict) 내에 'model' 키가 없습니다.")
                
                vectorizer = model_data.get('vectorizer')
                if vectorizer and hasattr(vectorizer, 'get_feature_names_out'):
                     print(f"      - 추출 특성 수   : {len(vectorizer.get_feature_names_out())} Features")
                
                label_encoder = model_data.get('label_encoder')
                if label_encoder and hasattr(label_encoder, 'classes_'):
                    print(f"      - Label Encoder  : {len(label_encoder.classes_)} Classes")
            else:
                print(f"      - 파일이 단순 객체이거나 예상된 Dict 구조가 아닙니다. (Type: {type(model_data)})")
                
        except Exception as e:
            print(f"   ❌ Pickle 분석 실패: {e}")

    print("\n------------------------------------------------------------\n")

    # Templates JSON check
    templates_path = files_config.get('templates', 'model/reply_templates_50.json')
    print(f"📋 [템플릿 정보] 경로: {templates_path}")
    meta = get_file_metadata(templates_path)
    if not meta:
        print(f"   ❌ 파일을 찾을 수 없습니다.")
    else:
        print(f"   ✅ 크기: {meta['size']} | 수정일: {meta['modified']}")
        try:
            with open(templates_path, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            
            if isinstance(templates_data, list):
                print(f"   🔍 세부 정보: 총 {len(templates_data)} 건의 템플릿 항목 포함 (목록 형태)")
            elif isinstance(templates_data, dict):
                print(f"   🔍 세부 정보: 총 {len(templates_data)} 건의 템플릿 항목 포함 (사전 형태)")
            else:
               print(f"   🔍 세부 정보: {type(templates_data)} 형태의 데이터") 
        except Exception as e:
            print(f"   ❌ JSON 분석 실패: {e}")

    print("\n" + "="*60)
    print("점검이 완료되었습니다.".center(55))
    print("="*60 + "\n")

if __name__ == '__main__':
    cwd = os.getcwd()
    if os.path.basename(cwd) == 'test':
        os.chdir('..')
    check_env()
