# Jira Backlog Mapping & Functional Specification
**Project**: 상담원 답변 자동 추천 시스템 (ReplyBot)
**Date**: 2026-02-04
**Author**: Artificial Intelligence Architect

본 문서는 소스 코드 분석 결과를 기반으로 도출된 Jira 등록용 백로그 목록입니다.
현재 구현된 실제 로직(Logic)을 중심으로 작성되었으며, 각 기능의 기술적 세부사항과 우선순위를 포함합니다.

## 1. Functional Breakdown (WBS)

| 대분류 (Epic) | 중분류 (Story/Task) | 기술적 세부사항 및 기능 설명 | 우선순위 |
| :--- | :--- | :--- | :--- |
| **🧠 AI Recommendation** | **Inference Pipeline** | **RandomForest 기반 추천 로직 구현**: <br>- `model/randomforest_model.pkl` 로드 및 검증 <br>- TF-IDF Vectorizer를 통한 입력 텍스트 벡터화 <br>- `predict_proba`를 이용한 상위 5개 후보군 도출 및 신뢰도(Confidence) 산출 | **Critical** |
| | **Text Preprocessing** | **Kiwi 형태소 분석기 연동**: <br>- 사용자 입력 쿼리에서 명사(NNG, NNP), 동사(VV), 형용사(VA) 등 핵심 품사 추출 <br>- 2글자 미만 및 불용어 필터링 로직 (`extract_morphological_keywords`) | **High** |
| | **Result Re-ranking** | **규칙 기반 후보 재순위화**: <br>- 특정 키워드(예: '변경', '교환') 감지 시 관련 템플릿의 가중치(1.5배) 부여 로직 <br>- 모델 예측 결과와 비즈니스 규칙의 하이브리드 적용 | **Medium** |
| | **Context Injection** | **동적 데이터 치환 시스템**: <br>- `ProductNameExtractor`를 통해 고객번호(Customer ID) 기반 상품명 조회 <br>- 템플릿 내 플레이스홀더(`★`, `{product_name}`)를 실제 상담 상품명으로 실시간 치환 | **High** |
| **🛡️ Security & Auth** | **Unified Auth Manager** | **통합 인증 관리 모듈**: <br>- `AuthManager` 클래스를 통한 사용자 생성, 인증, 정보 조회 통합 <br>- Argon2 알고리즘을 적용한 비밀번호 단방향 해싱 및 검증 | **High** |
| | **Session Management** | **DB 기반 세션 처리**: <br>- `active_sessions` 테이블을 활용한 서버 사이드 세션 관리 <br>- 중복 로그인 방지 및 세션 만료(1시간), IP/User-Agent 검증 | **High** |
| | **Account Lockout** | **계정 잠금 정책**: <br>- 5회 이상 로그인 실패 시 30분간 계정 자동 잠금 (`locked_until`) <br>- Brute-force 공격 방지 로직 구현 | **Medium** |
| | **Route Protection** | **미들웨어 기반 보안**: <br>- `SecurityMiddleware`를 통한 요청 가로채기 <br>- 화이트리스트(Login, Static 등) 제외 모든 경로에 대한 세션 유효성 강제 검사 | **High** |
| **📊 Dashboard & Data** | **Log Analytics** | **상담 이력 조회 및 필터링**: <br>- `DBLogger.get_logs`를 통한 기간별, 아이디별, 피드백 상태별 이력 조회 <br>- `/dashboard/api/logs` 엔드포인트 구현 | **Medium** |
| | **Feedback Loop** | **답변 수정 및 피드백 저장**: <br>- 상담원이 추천된 답변을 수동으로 수정 시 DB에 기록 (`update_manual_answer`) <br>- 향후 모델 재학습 데이터로 활용하기 위한 데이터 파이프라인 | **Low** |
| | **System Stats** | **실시간 현황 대시보드**: <br>- 일별 API 호출량, 템플릿 매칭 성공률 등 통계 데이터 시각화 API | **Low** |
| **⚙️ Infrastructure** | **App Initialization** | **Flask Application Factory**: <br>- `initialize_server()` 함수 내에서 ML 모델, DB, 로거의 순차적 비동기/동기 초기화 보장 <br>- Gunicorn 실행 환경을 고려한 Global Context 관리 | **Critical** |
| | **DB Connectivity** | **SQLAlchemy Connection Pool**: <br>- MySQL 8.4.6 연동 및 Connection Recycling(3600초) 설정 <br>- `db_session_maker`를 통한 Thread-safe 세션 배포 | **High** |
| | **Template Management** | **JSON 기반 템플릿 인덱싱**: <br>- `reply_templates_*.json` 파일 로드 및 ID 기반 해시맵(`templates_by_id`) 구축 <br>- 빠른 조회를 위한 인메모리 캐싱 구조 | **Medium** |

## 2. Technical Notes for Jira Configuration
- **Backend**: Python 3.12.9, Flask 3.x
- **Database**: MySQL 8.4.6 (`aidata` database)
- **Model**: Scikit-learn RandomForestClassifier (Pickle format)
- **Repo Location**: `c:\workspace\db\replybot`

이 문서는 엔터프라이즈 아키텍트 관점에서 소스 코드의 실제 구현체를 분석하여 작성되었습니다.
