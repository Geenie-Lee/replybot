#!/usr/bin/env python3
"""
Flask 기반 지능형 고객 응대 템플릿 추천 시스템
"""

import json
import os
import sys
import glob
import pickle
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from kiwipiepy import Kiwi
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, send_from_directory
from flask_cors import CORS
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# User defined modules
from auth_system.auth_core import AuthManager
from auth_system.middleware import SecurityMiddleware

from db_logger import DBLogger
from dashboard.routes import dashboard_bp
from system_management import system_bp
from product_name_extractor import ProductNameExtractor

try:
    import tomllib
except ImportError:
    import tomli as tomllib

# UTF-8 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 전역 변수
randomforest_classifier = None
product_extractor = None
kiwi_analyzer = None
db_logger = None

# Auth Globals
auth_manager = None
db_session_maker = None

templates_by_id = {}

# Model file paths
MODEL_FILE = "model/randomforest_model.pkl"
TEMPLATES_FILE = "model/reply_templates_80.json"

app = Flask(__name__, static_url_path='/assets', static_folder='static')
app.secret_key = os.urandom(24) # Flask Session Key
CORS(app)  # CORS 설정 추가

# Dashboard Blueprint 등록
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(system_bp, url_prefix='/system')

def initialize_server():
    """애플리케이션 팩토리 패턴 - RandomForest 모델 기반 초기화"""
    global randomforest_classifier, product_extractor, kiwi_analyzer, db_logger
    global auth_manager, db_session_maker
    
    try:
        # Config 로드 (DB 연결용)
        db_config = {}
        # Config 로드 (DB 연결용)
        db_config = {}
        if os.path.exists('config/config.toml'):
             with open('config/config.toml', 'rb') as f:
                toml_conf = tomllib.load(f)
                if toml_conf:
                    db_config = toml_conf.get('database', {})

        # DB 로거 초기화
        logger.info("🗄️ DB 로거 초기화 중...")
        try:
            db_logger = DBLogger(config_path='config/config.toml')
            app.config['DB_LOGGER'] = db_logger
            logger.info("✅ DB 로거 초기화 완료")
        except Exception as e:
            logger.error(f"⚠️ DB 로거 초기화 실패: {e}")

        # [Auth System] 초기화
        logger.info("🔐 인증 시스템 초기화 중...")
        try:
            # 1. SQLAlchemy Engine 생성
            user = db_config.get('user', 'root')
            password = db_config.get('password', '')
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 3306)
            dbname = db_config.get('database', 'aidata')
            
            # Connection string:
            db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
            engine = create_engine(db_uri, pool_recycle=3600)
            db_session_maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            # 2. 통합 AuthManager 생성
            auth_manager = AuthManager(db_session_maker)
            if not auth_manager.hasher:
                logger.warning("⚠️ [WARNING] AuthManager initialized without Argon2 Hasher! Passwords will fall back to plaintext check, causing failures for hashed passwords.")
            else:
                logger.info("✅ AuthManager initialized with Argon2 Hasher.")

            # 서버 재시작 시 기존 세션 모두 만료 처리 (사용자 요청사항)
            auth_manager.clear_all_sessions()

            # 3. Security Middleware 등록
            # NOTE: /assets prefix used to bypass Nginx /static block
            exempt = [r'^/login$', r'^/logout$', r'^/assets/.*', r'^/static/.*', r'^/dashboard/static/.*', r'^/favicon.ico$', r'^/api/messages$', r'^/register$']
            SecurityMiddleware(app, auth_manager, exempt_routes=exempt)
            
            # Make AuthManager accessible to blueprints
            app.config['AUTH_MANAGER'] = auth_manager
            
            logger.info("✅ 인증 시스템 초기화 완료 (Unified AuthManager)")

        except Exception as e:
            logger.error(f"⚠️ 인증 시스템 초기화 중 오류: {e}")


        # config.toml 로드 (재로드 - 파일경로 등)
        # ... (rest of original logic)
        if os.path.exists('config/config.toml'):
             with open('config/config.toml', 'rb') as f:
                toml_config = tomllib.load(f)
                if toml_config and 'files' in toml_config:
                    global MODEL_FILE, TEMPLATES_FILE
                    if 'model' in toml_config['files']: MODEL_FILE = toml_config['files']['model']
                    if 'templates' in toml_config['files']: TEMPLATES_FILE = toml_config['files']['templates'] 

        # 1. Kiwi 형태소 분석기 초기화
        logger.info("🔧 Kiwi 형태소 분석기 초기화 중...")
        kiwi_analyzer = Kiwi()
        logger.info("✅ Kiwi 형태소 분석기 초기화 완료")
        
        # 2. RandomForest 모델 로드
        logger.info(f"🤖 RandomForest 모델 로드 중: {MODEL_FILE}")
        if os.path.exists(MODEL_FILE):
            with open(MODEL_FILE, 'rb') as f:
                model_data = pickle.load(f)
            
            randomforest_classifier = model_data
            logger.info("✅ RandomForest 모델 로드 완료")
            logger.info(f"   - 모델 타입: {type(model_data['model']).__name__}")
            
            # 모델 데이터 구조 확인
            logger.debug(f"🔍 모델 데이터 키: {list(model_data.keys())}")
            
            if 'vectorizer' in model_data:
                logger.debug(f"   - 특성 수: {len(model_data['vectorizer'].get_feature_names_out())}")
            elif 'feature_names' in model_data:
                logger.debug(f"   - 특성 수: {len(model_data['feature_names'])}")
            
            if 'label_encoder' in model_data:
                logger.debug(f"   - 클래스 수: {len(model_data['label_encoder'].classes_)}")
            elif 'model' in model_data and hasattr(model_data['model'], 'classes_'):
                logger.debug(f"   - 클래스 수: {len(model_data['model'].classes_)}")
        else:
            logger.error(f"❌ 모델 파일을 찾을 수 없습니다: {MODEL_FILE}")
            return False
        
        # 3. 형태소 분석 템플릿 로드
        logger.info(f"📋 형태소 분석 템플릿 로드 중: {TEMPLATES_FILE}")
        if os.path.exists(TEMPLATES_FILE):
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            
            # 템플릿을 ID로 인덱싱
            global templates_by_id
            templates_by_id = {}
            templates_list = templates_data  # reply_templates_38.json은 배열 형태
            logger.info(f"📊 템플릿 데이터 구조: {len(templates_list)}개 템플릿 발견")
            
            for template in templates_list:
                template_id = template.get('id')
                if template_id is not None:
                    templates_by_id[template_id] = template
                    # 새로운 구조에 맞게 카테고리 정보 출력
                    category = template.get('inquiry_category', '제목없음')
                    version_type = template.get('version_type', '')
                    base_category = template.get('base_category', '')
                    
                    if version_type and base_category:
                        logger.debug(f"   - 템플릿 ID {template_id}: {base_category} ({version_type})")
                    else:
                        logger.debug(f"   - 템플릿 ID {template_id}: {category}")
                else:
                    logger.warning(f"⚠️ ID가 없는 템플릿 발견: {template.get('inquiry_category', '제목없음')}")
            
            logger.info(f"✅ {len(templates_by_id)}개 형태소 분석 템플릿 로드 완료")
            
            # 모델 클래스와 템플릿 ID 간의 매핑 확인
            if randomforest_classifier:
                if 'label_encoder' in randomforest_classifier:
                    model_classes = randomforest_classifier['label_encoder'].classes_
                elif 'model' in randomforest_classifier and hasattr(randomforest_classifier['model'], 'classes_'):
                    model_classes = randomforest_classifier['model'].classes_
                else:
                    model_classes = []
                
                if len(model_classes) > 0:
                    logger.info(f"🔍 모델 클래스와 템플릿 ID 매핑 확인:")
                    logger.info(f"   - 모델 클래스 수: {len(model_classes)}")
                    logger.debug(f"   - 사용 가능한 템플릿 ID: {sorted(list(templates_by_id.keys()))}")
                    
                    # 매핑되지 않는 클래스 확인
                    unmapped_classes = []
                    for class_id in model_classes:
                        if class_id not in templates_by_id:
                            unmapped_classes.append(class_id)
                    
                    if len(unmapped_classes) > 0:
                        logger.warning(f"⚠️ 매핑되지 않는 모델 클래스: {unmapped_classes}")
                        logger.warning(f"   - 이는 예측 오류를 발생시킬 수 있습니다")
                    else:
                        logger.info(f"✅ 모든 모델 클래스가 템플릿과 매핑됨")
        else:
            logger.error(f"❌ 템플릿 파일을 찾을 수 없습니다: {TEMPLATES_FILE}")
            return False
        
        # 4. 상품명 추출기 초기화
        product_extractor = ProductNameExtractor()
        logger.info("✅ 상품명 추출 및 치환 시스템 초기화 완료")
        
        logger.info("✅ RandomForest 기반 형태소 분석 시스템 초기화 완료")
        logger.info(f"📂 사용 중인 모델: {MODEL_FILE}")
        logger.info(f"📂 사용 중인 템플릿: {TEMPLATES_FILE}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 서버 초기화 실패: {e}")
        import traceback
        logger.error("Traceback:", exc_info=True)
        return False

def extract_morphological_keywords(text: str, consultation_type: str = "") -> List[str]:
    """텍스트에서 형태소 분석을 통해 키워드 추출 (상담유형 제외)"""
    if not text or not kiwi_analyzer:
        return []

    keywords = []

    try:
        # 문의내용만 형태소 분석 (상담유형 제외)
        result = kiwi_analyzer.analyze(text)

        # 중요한 품사태그
        important_pos = {'NNG', 'NNP', 'VV', 'VA', 'VX', 'MM', 'MAG', 'NNB', 'XSV', 'XSA'}
        
        for token in result[0][0]:
            form = token.form
            pos = token.tag
            
            # 중요한 품사이고 2글자 이상인 경우
            if pos in important_pos and len(form) >= 2:
                keywords.append(form)
            
            # 복합어 분해
            if len(form) >= 3:
                # 동사/형용사 어간 추출
                if pos in {'VV', 'VA', 'VX'}:
                    if form.endswith(('하다', '되다', '이다')):
                        base = form[:-2]  # '하다' 제거
                        if len(base) >= 2:
                            keywords.append(base)
                
                # 명사 복합어 처리
                elif pos in {'NNG', 'NNP'}:
                    if '취소' in form:
                        keywords.append('취소')
                    if '반품' in form:
                        keywords.append('반품')
                    if '교환' in form:
                        keywords.append('교환')
                    if '배송' in form:
                        keywords.append('배송')
                    if '환불' in form:
                        keywords.append('환불')
                    if '변경' in form:
                        keywords.append('변경')
        
        return keywords
        
    except Exception as e:
        logger.error(f"형태소 분석 오류: {e}")
        return []

def predict_template_with_randomforest(customer_keywords: List[str]) -> Dict:
    """RandomForest 모델을 사용하여 템플릿 예측"""
    logger.info(f"🔍 RandomForest 예측 시작: {len(customer_keywords)}개 키워드")
    
    if not randomforest_classifier:
        logger.error("❌ RandomForest 분류기가 초기화되지 않음")
        return None
    
    if not customer_keywords:
        logger.warning("❌ 고객 키워드가 없음")
        return None
    
    try:
        # 키워드를 텍스트로 변환
        keywords_text = ' '.join(customer_keywords)
        
        # TF-IDF 벡터화
        if 'vectorizer' in randomforest_classifier:
            vectorizer = randomforest_classifier['vectorizer']
            X_tfidf = vectorizer.transform([keywords_text])
            
            # 예측 (인덱스가 아닌 클래스 레이블이 반환됨)
            model = randomforest_classifier['model']
            prediction_label = model.predict(X_tfidf)[0]  # 이것은 템플릿 ID (문자열 또는 정수)
            probabilities = model.predict_proba(X_tfidf)[0]
            
            logger.debug(f"🎯 예측 결과(Label): {prediction_label} (타입: {type(prediction_label)})")
            
            # prediction_label을 정수로 변환
            try:
                best_template_id = int(prediction_label)
            except ValueError:
                logger.error(f"❌ 예측 레이블을 정수로 변환 불가: {prediction_label}")
                return None
            
            # 상위 5개 확률
            top_indices = np.argsort(probabilities)[::-1][:5]
            top_probabilities = []
            
            # 모델의 클래스 정보(템플릿 ID 목록)
            model_classes = model.classes_
            
            for idx in top_indices:
                # 인덱스를 실제 템플릿 ID로 매핑
                if idx < len(model_classes):
                    template_id = int(model_classes[idx])
                    top_probabilities.append({
                        'template_id': template_id,
                        'probability': float(probabilities[idx])
                    })
            
            # ---------------------------------------------------------
            # Rule-based Re-ranking (후처리 로직)
            # ---------------------------------------------------------
            if '변경' in customer_keywords:
                logger.info("💡 '변경' 키워드 감지됨. 순위 재조정 수행...")
                for prob in top_probabilities:
                    t_id = prob['template_id']
                    # 템플릿 메타데이터 조회
                    t_data = templates_by_id.get(t_id) if templates_by_id else None
                    if t_data:
                        # 제목이나 카테고리에 '변경' 또는 '교환'이 있으면 가중치 부여
                        title = t_data.get('title', '')
                        category = t_data.get('category', '')
                        inquiry_category = t_data.get('inquiry_category', '')
                        
                        target_text = f"{title} {category} {inquiry_category}"
                        if '변경' in target_text or '교환' in target_text:
                            original_prob = prob['probability']
                            # 가중치 1.2배 (최대 1.0 제한은 나중에 정렬만 하므로 굳이 안해도 됨)
                            prob['probability'] = original_prob * 1.5 
                            logger.debug(f"  Existing ID {t_id} Boost: {original_prob:.4f} -> {prob['probability']:.4f}")

                # 재정렬
                top_probabilities.sort(key=lambda x: x['probability'], reverse=True)
                
                # Best ID 갱신
                if top_probabilities:
                    new_best = top_probabilities[0]
                    if new_best['template_id'] != best_template_id:
                        logger.info(f"🔄 Re-ranking으로 Best 변경: {best_template_id} -> {new_best['template_id']}")
                        best_template_id = new_best['template_id']
            # ---------------------------------------------------------

            # prediction에 대한 신뢰도 찾기
            confidence = 0.0
            
            # 1. top_probabilities에서 찾기
            for prob in top_probabilities:
                if prob['template_id'] == best_template_id:
                    confidence = prob['probability']
                    break
            
            # 2. top_probabilities에 없다면 (확률이 낮아서 상위 5개에 안 든 경우 -> 이상하지만 처리)
            if confidence == 0.0:
                try:
                    # model.classes_에서 해당 ID의 인덱스를 찾아 확률 조회
                    # model.classes_의 타입에 따라 비교 방식 주의
                    if isinstance(model_classes[0], str):
                        class_idx = np.where(model_classes == str(best_template_id))[0][0]
                    else:
                        class_idx = np.where(model_classes == best_template_id)[0][0]
                    
                    confidence = float(probabilities[class_idx])
                except (IndexError, ValueError):
                    logger.error(f"⚠️ 예측 ID {best_template_id}의 인덱스를 classes_에서 찾을 수 없음")
                    # Fallback: 상위 1위 확률 사용
                    if top_probabilities:
                        best_template_id = top_probabilities[0]['template_id']
                        confidence = top_probabilities[0]['probability']
                        logger.warning(f"🔄 Fallback: 상위 1위 템플릿 ID {best_template_id} 사용")
            
            result = {
                'predicted_template_id': best_template_id,
                'confidence': confidence,
                'top_probabilities': top_probabilities,
                'input_keywords': customer_keywords
            }
            
            logger.info(f"✅ 예측 완료: 템플릿 ID {best_template_id}, 신뢰도 {result['confidence']:.6f}")
            return result
        else:
            logger.error("❌ vectorizer를 찾을 수 없습니다")
            return None
        
    except Exception as e:
        logger.error(f"RandomForest 예측 오류: {e}")
        import traceback
        logger.error("Exception in prediction:", exc_info=True)
        return None

# 반드시 initialize_server 정의보다 아래에 있어야 합니다.
with app.app_context():
    logger.info("🚀 Gunicorn/Flask 환경에서 시스템 초기화를 시작합니다...")
    if not initialize_server():
        logger.critical("❌ 시스템 초기화에 실패했습니다. 서버를 종료합니다.")
        sys.exit(1)

# 메시지 로드 함수
def get_messages():
    msg_file = 'config/messages.toml'
    default_messages = {
        "ko": {
            "common": {"page_title": "Wavve 라이브 콘텐츠 리플라이봇", "header_title": "Wavve 라이브 콘텐츠 리플라이봇"},
            "form": {"query_label": "문의내용 입력", "btn_generate": "생성"},
            "stats": {"total_templates": "총 템플릿"}
        },
        "en": {
            "common": {"page_title": "Wavve Live Content ReplyBot"},
            "form": {"query_label": "Enter Query", "btn_generate": "Generate"},
            "stats": {"total_templates": "Total Templates"}
        }
    }
    if os.path.exists(msg_file):
        try:
            with open(msg_file, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            logger.warning(f"⚠️ 메시지 파일 로드 실패: {e}")
            return default_messages
    return default_messages

def get_server_config_data():
    if os.path.exists('config/config.toml'):
        try:
            with open('config/config.toml', 'rb') as f:
                return tomllib.load(f) or {}
        except Exception as e:
            logger.error(f"Config Load Error: {e}")
    return {}

def get_current_theme():
    conf = get_server_config_data()
    return conf.get('server', {}).get('theme', 'mono')



@app.route('/login', methods=['GET', 'POST'])
def login():
    all_messages = get_messages()
    messages = all_messages.get('ko', {})
    current_theme = get_current_theme()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        client_ip = request.remote_addr

        if not username:
             return render_template('login.html', error="Please enter username.", messages=messages, i18n_messages=all_messages, current_theme=current_theme)

        if not auth_manager:
             return "Auth System Not Initialized", 500

        try:
            # 1. 인증 및 로그인
            # Note: result can be user_id (str) OR user_data (dict) if SETUP_REQUIRED
            success, msg, result = auth_manager.authenticate(username, password, client_ip)
            
            if success:
                # 2. 세션 발급
                user_id = result
                request_info = {
                    "ip": client_ip,
                    "user_agent": request.headers.get('User-Agent')
                }
                token = auth_manager.create_session(user_id, request_info)
                
                resp = make_response(redirect(url_for('index')))
                resp.set_cookie('session_token', token, httponly=True, samesite='Lax', max_age=3600)
                return resp
            
            elif msg == "SETUP_REQUIRED":
                # 비밀번호 초기 설정 필요
                return render_template('login.html', show_setup_password=True, setup_user=result, messages=messages, i18n_messages=all_messages, current_theme=current_theme)

            else:
                return render_template('login.html', error=msg, messages=messages, i18n_messages=all_messages, current_theme=current_theme)
        except Exception as e:
            logger.error(f"Login Error: {e}")
            return render_template('login.html', error="System Error", messages=messages, i18n_messages=all_messages, current_theme=current_theme)

    return render_template('login.html', messages=messages, i18n_messages=all_messages, current_theme=current_theme)

@app.route('/set_initial_password', methods=['POST'])
def set_initial_password():
    if request.is_json:
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
    else:
        user_id = request.form.get('user_id')
        password = request.form.get('password')

    if not user_id or not password:
        if request.is_json:
             return jsonify({"success": False, "error": "Missing required fields"})
        return "Missing fields", 400

    # auth_core.py updated to use ID in reset_password
    if auth_manager.reset_password(user_id, password):
        if request.is_json:
             return jsonify({"success": True, "message": "Password set successfully. Please login."})
        return redirect(url_for('login'))
    else:
        if request.is_json:
             return jsonify({"success": False, "error": "Failed to set password."})
        return "Failed", 500

@app.route('/register', methods=['POST'])
def register():
    all_messages = get_messages()
    messages = all_messages.get('ko', {})

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            user_id = data.get('user_id')
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
        else:
            user_id = request.form.get('user_id')
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
        
        if not all([user_id, username, password, email]):
             if request.is_json:
                 return jsonify({"success": False, "error": "All fields are required"})
             return render_template('login.html', register_error="All fields are required", show_register=True, messages=messages, i18n_messages=all_messages, current_theme=get_current_theme()) 
        
        if not auth_manager:
            if request.is_json:
                return jsonify({"success": False, "error": "Auth System Error"})
            return "Auth System Error", 500

        try:
            if auth_manager.create_user(user_id, username, password, email):
                if request.is_json:
                    return jsonify({"success": True, "message": "Registration successful. Please login."})
                return render_template('login.html', success="Registration successful. Please login.", messages=messages, i18n_messages=all_messages, current_theme=get_current_theme())
            else:
                if request.is_json:
                    return jsonify({"success": False, "error": "Registration failed. ID or Username may exist."})
                return render_template('login.html', register_error="Registration failed. ID or Username may exist.", show_register=True, messages=messages, i18n_messages=all_messages, current_theme=get_current_theme())
        except Exception as e:
            if request.is_json:
                 return jsonify({"success": False, "error": f"Error: {str(e)}"})
            return render_template('login.html', register_error=f"Error: {e}", show_register=True, messages=messages, i18n_messages=all_messages, current_theme=get_current_theme())
            
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    token = request.cookies.get('session_token')
    if token and auth_manager:
        auth_manager.logout(token)
    
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('session_token', '', expires=0)
    return resp

@app.route('/')
def index():
    """메인 페이지"""
    all_messages = get_messages()
    # 기본 언어 설정 (쿠키 등에서 가져올 수 있음, 현재는 ko 고정)
    messages = all_messages.get('ko', {})
    
    # config.yaml 로드하여 프론트엔드에 전달
    server_config = get_server_config_data()
    current_theme = server_config.get('server', {}).get('theme', 'mono')
            
    # Session Info (Current User)
    current_user = None
    token = request.cookies.get('session_token')
    
    if token and auth_manager:
        sess = auth_manager.get_session(token)
        if sess:
            current_user = dict(sess)
            
            # 사용자 이름 조회 (직접 DB 쿼리)
            if db_session_maker:
                db = db_session_maker()
                try:
                    user_res = db.execute(text("SELECT username, email FROM users WHERE id = :uid"), {"uid": sess['user_id']}).mappings().first()
                    if user_res:
                        current_user.update(dict(user_res))
                except Exception as e:
                    logger.error(f"User Info Fetch Error: {e}")
                finally:
                    db.close()

    return render_template('index.html', messages=messages, i18n_messages=all_messages, server_config=server_config, page_title=messages.get('common', {}).get('page_title', ''), current_user=current_user, current_theme=current_theme)

@app.route('/api/messages')
def api_messages():
    """메시지 목록 반환 API (프론트엔드 동적 로딩용)"""
    return jsonify(get_messages())


@app.route('/favicon.ico')
def favicon():
    """favicon 요청 무시 (204 No Content 반환)"""
    from flask import make_response
    response = make_response('', 204)
    response.headers['Content-Type'] = 'image/x-icon'
    return response

@app.route('/test')
def test_page():
    """템플릿 로딩 테스트 페이지"""
    try:
        with open('test_template_loading.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "<h1>테스트 페이지를 찾을 수 없습니다</h1>"

@app.route('/logo')
def logo():
    """로고 이미지 서빙 (경로 문제 해결)"""
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'), 'wavve.png')

@app.route('/api/find_template', methods=['POST'])
def find_template():
    """템플릿 찾기 API (RandomForest + 형태소 분석)"""
    try:
        # 초기화 확인
        if not randomforest_classifier:
            return jsonify({"success": False, "error": "시스템이 초기화되지 않았습니다"})
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "요청 데이터가 없습니다"})
        
        user_query = data.get('query', '').strip()
        context = data.get('context', '').strip()
        customer_number = data.get('customer_number', '').strip()
        
        if not user_query:
            return jsonify({"success": False, "error": "문의 내용이 비어있습니다"})
        
        # 상담 유형은 선택사항으로 변경 (RandomForest 모델에 직접 사용되지 않음)
        if not context:
            context = "기타"  # 기본값 설정
        
        logger.info(f"🔍 RandomForest 템플릿 매칭: '{user_query}' (유형: {context})")
        logger.debug(f"📊 디버그 - 입력 쿼리 길이: {len(user_query)}")
        logger.debug(f"📊 디버그 - 상담 유형: '{context}'")
        
        # 형태소 분석으로 키워드 추출 (문의내용만, 상담유형 제외)
        start_time = datetime.now()

        customer_keywords = extract_morphological_keywords(user_query)
        logger.debug(f"🔤 형태소 분석 결과: {customer_keywords}")
        logger.debug(f"📊 상담유형: '{context}' (제외됨) + 문의내용: '{user_query[:50]}...'")

        # RandomForest 모델로 템플릿 예측
        prediction_result = predict_template_with_randomforest(customer_keywords)
        
        if not prediction_result:
            return jsonify({
                "success": False,
                "error": "템플릿 예측에 실패했습니다",
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "method": "randomforest_morphological"
            })
        
        best_template_id = prediction_result['predicted_template_id']
        confidence = prediction_result['confidence']
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"📊 디버그 - 매칭 결과: ID {best_template_id}, 점수: {confidence:.6f}")
        logger.debug(f"📊 디버그 - 상위 확률:")
        for prob in prediction_result['top_probabilities'][:3]:
            logger.debug(f"    - 템플릿 {prob['template_id']}: {prob['probability']:.6f}")
        
        if best_template_id:  # 신뢰도 임계값 제거
            # 템플릿 조회
            template = templates_by_id.get(best_template_id)
            if not template:
                logger.error(f"❌ 템플릿 ID {best_template_id}를 찾을 수 없습니다")
                logger.info(f"📋 사용 가능한 템플릿 ID: {list(templates_by_id.keys())[:10]}...")
                
                # Fallback: 상위 확률 중에서 존재하는 템플릿 찾기
                fallback_template = None
                fallback_id = None
                
                for prob in prediction_result['top_probabilities']:
                    if prob['template_id'] in templates_by_id:
                        fallback_template = templates_by_id[prob['template_id']]
                        fallback_id = prob['template_id']
                        logger.warning(f"🔄 Fallback: 템플릿 ID {fallback_id} 사용 (신뢰도: {prob['probability']:.6f})")
                        break
                
                if fallback_template:
                    # Fallback 템플릿으로 처리 계속
                    template = fallback_template
                    best_template_id = fallback_id
                    confidence = prediction_result['top_probabilities'][0]['probability']  # 원래 예측의 신뢰도 유지
                    logger.info(f"✅ Fallback 템플릿으로 계속 처리: ID {fallback_id}")
                else:
                    return jsonify({
                        "success": False,
                        "error": f"예측된 템플릿 ID {best_template_id}를 찾을 수 없습니다",
                        "confidence": float(confidence),
                        "processing_time": processing_time,
                    "method": "randomforest_morphological"
                })
            
            # 고객번호로 상품명 및 상담원 답변 조회
            original_template_text = template.get('general_template', template.get('template_text', template.get('content', '')))
            product_name = None
            agent_response = None
            
            if product_extractor:
                # 고객번호가 있으면 상품명과 상담원 답변 조회
                if customer_number:
                    product_name = product_extractor.get_product_name_by_customer(customer_number)
                    agent_response = product_extractor.get_agent_response_by_customer(customer_number)
                
                # 템플릿 치환 (상품명이 있으면 사용, 없으면 일반적인 치환)
                if original_template_text:
                    replaced_template_text = product_extractor.replace_template_placeholders_with_product(
                        original_template_text, user_query, customer_number, context, product_name
                    )
                    logger.debug(f"📝 템플릿 치환: '{original_template_text[:50]}...' → '{replaced_template_text[:50]}...'")
                    if product_name:
                        logger.info(f"🏷️ 상품명 치환: '{product_name}'")
                else:
                    replaced_template_text = original_template_text
            else:
                replaced_template_text = original_template_text
            
            # Top 3 템플릿 정보 수집
            top_templates = []
            if prediction_result and 'top_probabilities' in prediction_result:
                for prob in prediction_result['top_probabilities'][:3]:
                    t_id = prob['template_id']
                    t_conf = prob['probability']
                    
                    if t_id in templates_by_id:
                        t_data = templates_by_id[t_id]
                        
                        # 텍스트 가져오기
                        t_orig_text = t_data.get('general_template', t_data.get('template_text', t_data.get('content', '')))
                        
                        # 치환 적용
                        t_repl_text = t_orig_text
                        if product_extractor and t_orig_text:
                            # 이미 조회된 product_name 사용
                            t_repl_text = product_extractor.replace_template_placeholders_with_product(
                                t_orig_text, user_query, customer_number, context, product_name
                            )
                        
                        top_templates.append({
                            "id": t_id,
                            "title": t_data.get('inquiry_category', t_data.get('title', '')),
                            "content": t_repl_text,
                            "confidence": float(t_conf),
                            "category": t_data.get('inquiry_category', t_data.get('category', '')),
                            "template_type": t_data.get('template_type', '일반')
                        })
            
            response = jsonify({
                "success": True,
                "template": {
                    "id": best_template_id,
                    "title": template.get('inquiry_category', template.get('title', '')),
                    "content": replaced_template_text,
                    "template_text": replaced_template_text,
                    "original_template": original_template_text,  # 원본 템플릿 추가
                    "category": template.get('inquiry_category', template.get('category', '')),
                    "template_type": template.get('template_type', '템플릿'),
                    "version_type": template.get('version_type', ''),
                    "base_category": template.get('base_category', '')
                },
                "top_templates": top_templates,
                "confidence": float(confidence),
                "processing_time": processing_time,
                "method": "randomforest_morphological",
                "morphological_keywords": customer_keywords,
                "reason": f"RandomForest 모델로 신뢰도 {confidence:.3f} 달성",
                "customer_number": customer_number,
                "consultation_type": context,
                "product_name": product_name,
                "agent_response": agent_response,
                "product_replacement_applied": bool(product_name and original_template_text != replaced_template_text)
            })

            # Top 3 템플릿 ID 리스트 생성
            top_template_ids = [t['id'] for t in top_templates]

            # 로그 비동기 저장
            log_id = None
            if db_logger:
                # Get Current User ID from Token
                current_user_id = None
                token = request.cookies.get('session_token')
                if token and auth_manager:
                    session_data = auth_manager.get_session(token)
                    if session_data:
                        current_user_id = session_data.get('user_id')

                log_id = db_logger.log_query(
                    customer_number, 
                    context, 
                    user_query, 
                    best_template_id, 
                    confidence, 
                    processing_time, 
                    request.remote_addr,
                    top_template_ids,
                    user_id=current_user_id
                )
            
             # log_id를 응답에 포함
            response_data = response.get_json()
            if response_data:
                response_data['log_id'] = log_id
                return jsonify(response_data)
            return response
        else:
            response = jsonify({
                "success": False,
                "error": "적합한 템플릿을 찾을 수 없습니다",
                "confidence": float(confidence) if confidence else 0.0,
                "processing_time": processing_time,
                "method": "randomforest_morphological",
                "morphological_keywords": customer_keywords
            })

            if db_logger:
                 log_id = db_logger.log_query(
                    customer_number, 
                    context, 
                    user_query, 
                    None, 
                    0.0, 
                    processing_time, 
                    request.remote_addr
                )
                 # 실패 시에도 log_id 반환 (피드백 가능하도록)
                 response_data = response.get_json()
                 if response_data:
                     response_data['log_id'] = log_id
                     return jsonify(response_data)
            return response
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_msg = traceback.format_exc()
        logger.error(f"❌ 템플릿 매칭 오류: {error_msg}")
        logger.error(f"❌ 상세 오류:\n{traceback_msg}")
        return jsonify({
            "success": False, 
            "error": f"서버 오류: {error_msg}",
            "details": traceback_msg if app.debug else None
        }), 500

@app.route('/api/templates')
def get_templates():
    """템플릿 목록 조회"""
    try:
        if not templates_by_id:
            return jsonify({"error": "템플릿 데이터가 없습니다"})
        
        templates_list = []
        for template_id, template in templates_by_id.items():
            # 새로운 구조에 맞게 카테고리 정보 구성
            category = template.get('inquiry_category', template.get('title', ''))
            version_type = template.get('version_type', '')
            base_category = template.get('base_category', '')
            
            # 카테고리 표시명 구성 (사용자 요청: inquiry_category 사용)
            # if version_type and base_category:
            #     display_category = f"{base_category} ({version_type})"
            # else:
            #     display_category = category
            
            # 80개 템플릿의 경우 inquiry_category 사용
            display_category = category

            template_info = {
                "id": template_id,
                "title": display_category,
                "category": display_category,
                "template_type": template.get('template_type', '일반'),
                "version_type": version_type,
                "base_category": base_category,
                "raw_inquiry_category": category,
                "full_content": template.get('general_template', template.get('template_text', template.get('content', ''))),
                "template_text": template.get('general_template', template.get('template_text', template.get('content', '')))[:200] + "..." if len(template.get('general_template', template.get('template_text', template.get('content', '')))) > 200 else template.get('general_template', template.get('template_text', template.get('content', '')))
            }
            templates_list.append(template_info)
        
        return jsonify({
            "success": True,
            "templates": templates_list,
            "count": len(templates_list)
        })
    except Exception as e:
        return jsonify({"error": f"템플릿 조회 오류: {str(e)}"})

@app.route('/api/stats')
def get_stats():
    """시스템 통계"""
    try:
        template_count = len(templates_by_id) if templates_by_id else 0
        model_type = type(randomforest_classifier['model']).__name__ if randomforest_classifier else 'N/A'
        
        if randomforest_classifier:
            if 'vectorizer' in randomforest_classifier:
                feature_count = len(randomforest_classifier['vectorizer'].get_feature_names_out())
            elif 'feature_names' in randomforest_classifier:
                feature_count = len(randomforest_classifier['feature_names'])
            else:
                feature_count = 0
            
            if 'label_encoder' in randomforest_classifier:
                class_count = len(randomforest_classifier['label_encoder'].classes_)
            elif 'model' in randomforest_classifier and hasattr(randomforest_classifier['model'], 'classes_'):
                class_count = len(randomforest_classifier['model'].classes_)
            else:
                class_count = 0
        else:
            feature_count = 0
            class_count = 0
        
        # 카테고리별 통계
        categories = {}
        base_categories = {}
        if templates_by_id:
            for template in templates_by_id.values():
                category = template.get('inquiry_category', template.get('category', '기타'))
                base_category = template.get('base_category', category)
                version_type = template.get('version_type', '')
                
                # 전체 카테고리 통계
                categories[category] = categories.get(category, 0) + 1
                
                # 기본 카테고리별 통계
                if base_category:
                    if base_category not in base_categories:
                        base_categories[base_category] = {'total': 0, 'versions': {}}
                    base_categories[base_category]['total'] += 1
                    
                    if version_type:
                        base_categories[base_category]['versions'][version_type] = base_categories[base_category]['versions'].get(version_type, 0) + 1
        
        # 기본 응답 데이터
        response_data = {
            "total_templates": template_count,
            "model_type": model_type,
            "feature_count": feature_count,
            "class_count": class_count,
            "categories": categories,
            "base_categories": base_categories,
            "server_status": "running",
            "processing_mode": "randomforest_morphological",
            "morphological_analyzer": "Kiwi"
        }

        # DB 로그 통계 병합
        if db_logger:
            try:
                db_stats = db_logger.get_dashboard_stats()
                if db_stats:
                    response_data.update(db_stats)
            except Exception as dbe:
                logger.error(f"DB Log Stats Error: {dbe}")

        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": f"통계 조회 오류: {str(e)}"})

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    """사용자가 입력한 정답(피드백) 저장 API"""
    try:
        data = request.get_json()
        log_id = data.get('log_id')
        manual_answer = data.get('manual_answer')
        manual_category = data.get('manual_category') # 텍스트 (Legacy or Display)
        template_id = data.get('template_id') # New

        if not log_id or not manual_answer:
            return jsonify({"success": False, "error": "필수 데이터 누락"})

        current_user_id = None
        if auth_manager:
            token = request.cookies.get('session_token')
            if token:
                sess = auth_manager.get_session(token)
                if sess:
                    current_user_id = sess.get('user_id')

        # 템플릿 ID가 없고 카테고리만 있는 경우 (기존 호환성 or 매칭 시도)
        # 하지만 프론트엔드에서 ID를 보내도록 변경 예정.
        
        if db_logger:
            # save_manual_feedback (Reverted to update_manual_answer)
            # template_id는 사용하지 않음 (로그 테이블에는 manual_category 텍스트 저장)
            success = db_logger.update_manual_answer(log_id, manual_answer, manual_category, user_id=current_user_id)
            if success:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "DB 업데이트 실패"})
        
        return jsonify({"success": False, "error": "DB Logger 없음"})


    except Exception as e:
        logger.error(f"❌ 피드백 저장 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/morphological_analysis', methods=['POST'])
def analyze_morphological():
    """형태소 분석 API (상담유형 + 문의내용)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "요청 데이터가 없습니다"})
        
        text = data.get('text', '').strip()
        consultation_type = data.get('consultation_type', '').strip()

        if not text:
            return jsonify({"success": False, "error": "분석할 텍스트가 없습니다"})

        # 상담유형이 없으면 기본값 설정
        if not consultation_type:
            consultation_type = "기타"
        
        # 형태소 분석 수행 (문의내용만, 상담유형 제외)
        keywords = extract_morphological_keywords(text)

        # 상담유형 키워드와 문의내용 키워드 분리
        type_keywords = []
        content_keywords = []

        if consultation_type:
            # 상담유형만 분석 (참고용)
            type_keywords = extract_morphological_keywords(consultation_type)
            # 문의내용만 분석
            content_keywords = extract_morphological_keywords(text)
        
        return jsonify({
            "success": True,
            "original_text": text,
            "consultation_type": consultation_type,
            "morphological_keywords": keywords,
            "type_keywords": type_keywords,
            "content_keywords": content_keywords,
            "keywords_count": len(keywords),
            "type_keywords_count": len(type_keywords),
            "content_keywords_count": len(content_keywords),
            "analyzer": "Kiwi"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"형태소 분석 오류: {str(e)}"
        }), 500

# Gunicorn 등 WSGI 서버 환경에서 실행 시 초기화 수행
# __name__이 'web_server'일 때도 실행되어야 함
if __name__ != "__main__":
    logger.info("🚀 WSGI(Gunicorn) 환경 감지: 서버 초기화를 시작합니다...")
    if not initialize_server():
        logger.error("❌ WSGI 초기화 실패")

if __name__ == '__main__':
    logger.info("🌐 === 신세계 라이브쇼핑 RandomForest 템플릿 매칭 웹 서버 ===")
    logger.info("형태소 분석 + RandomForest 모델 기반")
    logger.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    # 서버 초기화
    if initialize_server():
        logger.info("\n🚀 웹 서버를 시작합니다...")
        logger.info("📱 웹 인터페이스: http://localhost:5000")
        logger.info("🔧 API 엔드포인트: http://localhost:5000/api/find_template")
        logger.info("🔤 형태소 분석 API: http://localhost:5000/api/morphological_analysis")
        
        # Flask 개발 서버 실행
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    else:
        logger.critical("❌ 서버 초기화 실패로 종료합니다")
