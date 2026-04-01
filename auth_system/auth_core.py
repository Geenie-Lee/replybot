import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

# 비밀번호 보안 라이브러리 (없으면 Fallback)
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
except ImportError:
    PasswordHasher = None

class AuthManager:
    """
    [통합 인증 관리자]
    복잡한 객체지향 구조를 제거하고, 하나의 클래스에서 인증과 세션을 모두 처리합니다.
    """
    def __init__(self, db_session_maker):
        # 1. DB 연결 도구 저장 (`web_server.py` 에서 넘겨받음)
        self.db_maker = db_session_maker
        
        # 2. 기본 보안 설정
        self.session_lifetime_hours = 1     # 세션 유지 시간
        self.max_login_fails = 5            # 최대 로그인 실패 횟수
        self.lockout_time_minutes = 30      # 계정 잠금 시간
        
        # 3. 비밀번호 해싱 도구 준비
        if PasswordHasher:
            self.hasher = PasswordHasher()
        else:
            self.hasher = None
            print("⚠️ Argon2 라이브러리가 없어 기본 보안이 약화됩니다.")

    def _get_db(self):
        """DB 세션을 생성하는 내부 함수"""
        return self.db_maker()

    # ------------------------------------------------------------------
    # 1. 사용자 관리 (회원가입, 조회)
    # ------------------------------------------------------------------

    def create_user(self, user_id: str, username: str, password: str, email: str, group_id: int = 2) -> bool:
        """새 사용자를 생성합니다."""
        db = self._get_db()
        try:
            # 비밀번호 암호화
            if self.hasher:
                pw_hash = self.hasher.hash(password)
            else:
                pw_hash = password # 보안 취약 (데모용)
            
            sql = text("""
                INSERT INTO users (id, username, email, password_hash, group_id)
                VALUES (:id, :username, :email, :hash, :group_id)
            """)
            db.execute(sql, {
                "id": user_id,
                "username": username,
                "email": email,
                "hash": pw_hash,
                "group_id": group_id
            })
            db.commit()
            return True
        except Exception as e:
            print(f"❌ 사용자 생성 실패: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def _get_user_info(self, identifier: str):
        """DB에서 사용자 정보 조회 (ID만 체크)"""
        db = self._get_db()
        try:
            sql = text("SELECT * FROM users WHERE id = :u")
            result = db.execute(sql, {"u": identifier}).mappings().first()
            return dict(result) if result else None
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 2. 인증 로직 (로그인 시도)
    # ------------------------------------------------------------------

    def authenticate(self, username: str, password: str, ip_address: str) -> Tuple[bool, str, Any]:
        """
        아이디/비번을 검사합니다.
        반환값: (성공여부, 메시지, 사용자ID 또는 사용자객체)
        """
        user = self._get_user_info(username)
        db = self._get_db() # 잠금 카운트 업데이트용 세션
        
        # 사용자 없음
        if not user:
            return False, "존재하지 않는 사용자입니다.", None
        
        try:
            # A. 계정 잠금 확인
            if user['is_locked']:
                if user['locked_until'] and user['locked_until'] > datetime.now():
                    return False, "계정이 잠겨있습니다. 잠시 후 다시 시도하세요.", None
                else:
                    # 잠금 해제 (시간 경과)
                    self._reset_fail_count(db, user['id'])

            # B. 비밀번호 검사
            valid = False
            stored_hash = user.get('password_hash', '')
            
            # [신규] 비밀번호가 DB에 없는 경우 -> 초기 설정이 필요함
            if not stored_hash:
                 return False, "SETUP_REQUIRED", user

            if stored_hash and stored_hash.startswith('$argon2'):
                if not self.hasher:
                    print(f"❌ Critical: User '{username}' has Argon2 hash but Argon2 library is missing.")
                    return False, "보안 모듈(Argon2)이 서버에 설치되지 않았습니다.", None
                
                try:
                    self.hasher.verify(stored_hash, password)
                    valid = True
                except:
                    valid = False
            else:
                # 일반 텍스트 비교 (또는 해시가 아닌 경우)
                valid = (stored_hash == password)

            # C. 결과 처리
            if valid:
                self._reset_fail_count(db, user['id'])
                db.commit()
                return True, "로그인 성공", user['id']
            else:
                self._increase_fail_count(db, user['username'])
                db.commit()
                return False, "비밀번호가 일치하지 않습니다.", None

        except Exception as e:
            print(f"인증 오류: {e}")
            return False, "시스템 오류", None
        finally:
            db.close()

    def _reset_fail_count(self, db_session, user_id):
        db_session.execute(text("UPDATE users SET failed_login_count=0, is_locked=0, locked_until=NULL WHERE id=:uid"), {"uid": user_id})

    def _increase_fail_count(self, db_session, username):
        sql = text("""
            UPDATE users 
            SET failed_login_count = failed_login_count + 1,
                is_locked = CASE WHEN failed_login_count >= :max THEN 1 ELSE 0 END,
                locked_until = CASE WHEN failed_login_count >= :max THEN DATE_ADD(NOW(), INTERVAL :lock_min MINUTE) ELSE NULL END
            WHERE username = :u
        """)
        db_session.execute(sql, {"u": username, "max": self.max_login_fails, "lock_min": self.lockout_time_minutes})

    def verify_user_for_reset(self, username: str, email: str) -> bool:
        """비밀번호 재설정을 위해 사용자 정보를 확인합니다."""
        user = self._get_user_info(username)
        if user and user['email'] == email:
            return True
        return False

    def reset_password(self, username: str, new_password: str) -> bool:
        """비밀번호를 재설정합니다 (ID 기준 Update)."""
        db = self._get_db()
        try:
            if self.hasher:
                pw_hash = self.hasher.hash(new_password)
            else:
                pw_hash = new_password
            
            db.execute(text("UPDATE users SET password_hash = :h, failed_login_count=0, is_locked=0 WHERE id = :u"), 
                      {"h": pw_hash, "u": username})
            db.commit()
            return True
        except Exception as e:
            print(f"Password reset failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 3. 세션 관리 (로그인 후 토큰 처리)
    # ------------------------------------------------------------------

    def create_session(self, user_id: str, client_info: Dict) -> str:
        """세션 토큰을 발급하고 DB에 저장합니다."""
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=self.session_lifetime_hours)
        
        db = self._get_db()
        try:
            sql = text("""
                INSERT INTO active_sessions (session_id, user_id, ip_address, user_agent, expires_at)
                VALUES (:token, :uid, :ip, :ua, :exp)
            """)
            db.execute(sql, {
                "token": token, "uid": user_id,
                "ip": client_info.get('ip'), "ua": client_info.get('user_agent'),
                "exp": expiry
            })
            
            # 마지막 로그인 시간 업데이트
            db.execute(text("UPDATE users SET last_login_at = NOW() WHERE id = :uid"), {"uid": user_id})
            db.commit()
            return token
        except Exception as e:
            print(f"세션 생성 실패: {e}")
            db.rollback()
            return ""
        finally:
            db.close()

    def get_session(self, token: str) -> Optional[Dict]:
        """토큰으로 세션 정보를 조회합니다."""
        if not token: return None
        
        db = self._get_db()
        try:
            sql = text("""
                SELECT session_id, user_id, ip_address as ip, user_agent, expires_at 
                FROM active_sessions 
                WHERE session_id = :t AND expires_at > NOW()
            """)
            result = db.execute(sql, {"t": token}).mappings().first()
            return dict(result) if result else None
        finally:
            db.close()

    def logout(self, token: str):
        """세션을 삭제합니다."""
        db = self._get_db()
        try:
            db.execute(text("DELETE FROM active_sessions WHERE session_id = :t"), {"t": token})
            db.commit()
        finally:
            db.close()

    def clear_all_sessions(self):
        """서버 시작 시 모든 세션을 초기화합니다."""
        db = self._get_db()
        try:
            db.execute(text("DELETE FROM active_sessions"))
            db.commit()
            print("🧹 모든 활성 세션이 초기화되었습니다.")
        except Exception as e:
            print(f"⚠️ 세션 초기화 실패: {e}")
        finally:
            db.close()

