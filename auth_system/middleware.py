from flask import Request, Response, session, g, request, abort, redirect
from typing import Callable
from .auth_core import AuthManager
import re

class SecurityMiddleware:
    """
    [보안 미들웨어]
    모든 요청에 대해 인증 여부를 검사하고, 보안 헤더를 추가합니다.
    """
    def __init__(self, app, auth_manager: AuthManager, exempt_routes=None):
        self.app = app
        self.auth_manager = auth_manager
        self.exempt_routes = exempt_routes or [] 
        
        self.app.before_request(self.process_request)
        self.app.after_request(self.process_response)

    def is_exempt(self, path: str) -> bool:
        for route in self.exempt_routes:
            if re.match(route, path):
                return True
        return False

    def process_request(self):
        """요청 전처리: 인증 검사"""
        path = request.path
        
        if path.startswith('/static') or path.startswith('/assets') or self.is_exempt(path):
            return None 

        token = request.cookies.get('session_token')
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            if request.is_json or path.startswith('/api'):
                return abort(401, description="Authentication required")
            return redirect('/login')

        # AuthManager를 통해 세션 검증
        session_data = self.auth_manager.get_session(token)
        if not session_data:
            if request.is_json:
                return abort(401, description="Invalid or expired session")
            return redirect('/login') 

        g.user_id = session_data.get('user_id')
        g.token = token

    def process_response(self, response: Response):
        """응답 후처리: 보안 헤더"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response
