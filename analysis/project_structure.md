# Project Structure & Key Features
**Project**: 상담원 답변 자동 추천 시스템 (ReplyBot)
**Generated Date**: 2026-02-05

## 📂 Directory Tree

```bash
replybot/
├── analysis/               # [NEW] 분석 결과 및 산출물 저장
│   ├── jira_backlog_mapping.md   # 기능 명세 및 Jira 백로그 매핑
│   └── project_structure.md      # (본 파일) 프로젝트 구조도
├── auth_system/            # 인증 및 보안 모듈
│   ├── auth_core.py        # AuthManager: 통합 인증 로직 (로그인, 세션 생성)
│   ├── middleware.py       # SecurityMiddleware: 요청 필터링 및 세션 검증
│   └── schema.sql          # 사용자 및 세션 DB 스키마 정의
├── config/                 # 설정 파일
│   ├── config.toml         # DB 접속 정보, 파일 경로 등 시스템 설정
│   └── messages.toml       # 다국어(i18n) UI 메시지 팩
├── dashboard/              # 관리자 대시보드 Blueprint
│   ├── routes.py           # 통계 API 및 화면 라우팅
│   ├── static/             # 대시보드 전용 정적 리소스 (JS/CSS)
│   └── templates/          # 대시보드 HTML 템플릿
├── model/                  # AI 모델 및 데이터셋
│   ├── randomforest_model.pkl    # 학습된 RandomForest 분류 모델
│   ├── reply_templates_80.json   # 답변 템플릿 데이터 (ID 매핑용)
│   ├── enhanced_ubase_agent_unified.json  # 고객-상품 매핑 메타데이터
│   └── source/             # 원본 학습 데이터
├── static/                 # 공통 정적 리소스
│   ├── css/                # 메인 스타일시트
│   ├── js/                 # 메인 프론트엔드 로직
│   └── vendor/             # 외부 라이브러리 (Bootstrap, jQuery 등)
├── system_management/      # 시스템 관리 기능 (Blueprints)
├── templates/              # 메인 웹 페이지 HTML 템플릿
│   ├── index.html          # 메인 챗봇/추천 인터페이스
│   ├── login.html          # 로그인 페이지
│   └── error.html          # 에러 페이지
├── test/                   # 단위 테스트 및 검증 스크립트
├── db_logger.py            # DB 로깅 유틸리티 (상담 이력 저장/조회)
├── product_name_extractor.py     # 상품명 추출 및 템플릿 치환 로직
├── web_server.py           # [MAIN] Flask 애플리케이션 진입점 및 초기화
└── requirements.txt        # Python 의존성 목록
```

## 🔑 Key Features Overview

| Feature Module | Files | Description |
| :--- | :--- | :--- |
| **Main Server** | `web_server.py` | • Flask 앱 초기화 및 Gunicorn 연동<br>• RandomForest 모델 및 전역 객체(Logger, Auth) 로드<br>• 메인 API 엔드포인트 (`/api/find_template` 등) 처리 |
| **Authentication** | `auth_system/auth_core.py` | • Argon2 기반 비밀번호 해싱 및 검증<br>• DB 기반 세션 관리 (`active_sessions` 테이블)<br>• 로그인 실패 시 계정 잠금 정책 구현 |
| **AI Engine** | `product_name_extractor.py`<br>`model/*.pkl` | • RandomForest 기반 최적 템플릿 추천 (TF-IDF)<br>• 형태소 분석(Kiwi)을 통한 키워드 추출<br>• 정규식 기반 상품명 자동 치환 및 마스킹 |
| **Dashboard** | `dashboard/routes.py`<br>`db_logger.py` | • 상담 이력 및 추천 피드백 데이터 시각화<br>• 날짜별/유형별 필터링 기능 제공<br>• 수동 답변 수정 내역 DB 업데이트 |
| **Configuration** | `config/*.toml` | • 환경 변수 분리 (DB 접속정보, 모델 경로)<br>• 다국어 안내 메시지 통합 관리 |

## 🛠️ Tech Stack & Attributes
- **Framework**: Flask (Python 3.12.9)
- **Database**: MySQL 8.4.6
- **ML/NLP**: Scikit-learn (RandomForest), Kiwi (Morphological Analysis)
- **Frontend**: HTML5, jQuery, Tailwind CSS
- **Security**: Argon2 Hashing, Session Cookies
