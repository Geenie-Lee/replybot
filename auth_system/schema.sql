-- 엔터프라이즈급 인증 시스템을 위한 DB 스키마
-- MySQL 8.4+ 호환

CREATE DATABASE IF NOT EXISTS aidata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aidata;

-- 1. 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY, -- 외부 포탈 ID 연동을 위해 자동 증가 제거 및 문자열 변경
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    
    -- 계정 상태 관리
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_until DATETIME NULL,
    failed_login_count INT DEFAULT 0,
    
    -- 감사 로그용
    last_login_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_users_username (username),
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

-- 2. 로그인 시도 로그 (Brute-force 방지용)
CREATE TABLE IF NOT EXISTS login_attempts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100), -- 존재하지 않는 유저명도 기록하여 공격 분석
    ip_address VARCHAR(45) NOT NULL, -- IPv6 대응
    user_agent VARCHAR(255),
    attempt_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    was_successful BOOLEAN DEFAULT FALSE,
    
    -- 파티셔닝 또는 주기적 삭제(Cleanup) 고려 필요
    INDEX idx_attempt_check (username, ip_address, attempt_time),
    INDEX idx_ip_time (ip_address, attempt_time) -- IP 기반 차단용
) ENGINE=InnoDB;

-- 3. 활성 세션 (선택적: Redis를 사용하지 못하는 백업 환경용)
CREATE TABLE IF NOT EXISTS active_sessions (
    session_id VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_expiry (expires_at)
) ENGINE=InnoDB;
