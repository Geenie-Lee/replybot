import os
import time
import jwt
from flask import Flask, render_template_string, request, url_for, redirect
from sqlalchemy import create_engine, text

try:
    import tomllib
except ImportError:
    import tomli as tomllib

app = Flask(__name__)

# Config 로드
config_path = os.path.join(app.root_path, 'config', 'config.toml')
db_uri = None
jwt_secret = ""
replybot_port = 5000

if os.path.exists(config_path):
    with open(config_path, 'rb') as f:
        conf = tomllib.load(f)
        db_conf = conf.get('database', {})
        user = db_conf.get('user', 'root')
        password = db_conf.get('password', '')
        host = db_conf.get('host', 'localhost')
        port = db_conf.get('port', 3306)
        dbname = db_conf.get('database', 'aidata')
        db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
        
        server_conf = conf.get('server', {})
        replybot_port = server_conf.get('port', 5000)
        jwt_secret = server_conf.get('jwt_secret', 'your_jwt_secret_key_here')

engine = create_engine(db_uri) if db_uri else None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mock 포탈 시스템</title>
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        h1 { border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; color: #1e293b; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #cbd5e1; padding: 12px; text-align: left; }
        th { background-color: #f8fafc; font-weight: bold; }
        .btn { background-color: #3b82f6; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; }
        .btn:hover { background-color: #2563eb; }
        .admin-badge { background-color: #ef4444; color: white; padding: 2px 6px; border-radius: 12px; font-size: 11px; }
    </style>
    <script>
        function openReplyBot(url) {
            // 새 창(팝업)으로 리플라이봇 열기
            window.open(url, 'replybot', 'width=1000,height=800,menubar=no,toolbar=no,location=no,status=no');
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>[Mock] 사내 포탈 시스템</h1>
        <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
            <p style="margin: 0;">현재 포탈 시스템에 등록된 사용자 목록입니다. (DB: users 테이블)</p>
            <a href="/sample" class="btn" style="background-color: #10b981;">👉 외부 API 연동 샘플 보기</a>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>사용자 ID</th>
                    <th>이름</th>
                    <th>권한</th>
                    <th>[앱] 리플라이봇 연동</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td>{{ user.id }}</td>
                    <td>{{ user.username }}</td>
                    <td>
                        {% if user.admin_yn == 'Y' %}
                        <span class="admin-badge">Admin</span>
                        {% else %}
                        일반
                        {% endif %}
                    </td>
                    <td>
                        <button class="btn" onclick="openReplyBot('/generate_sso_link?user_id={{ user.id }}')">
                            리플라이봇 열기 (SSO)
                        </button>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="4" style="text-align: center;">사용자가 없습니다.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    if not engine:
        return "DB 설정 오류", 500
        
    users = []
    try:
        with engine.connect() as conn:
            # admin_yn 이 없으면 추가되는 중일 수도 있으니 조회 시 방어 로직
            # 단, 앞서 user_res 쿼리 수정 시 오류가 없었다면 존재한다고 가정
            sql = text("SELECT id, username, email, admin_yn FROM users")
            result = conn.execute(sql).mappings().all()
            users = [dict(row) for row in result]
    except Exception as e:
        users = []
        print(f"Error reading users: {e}")
        
    return render_template_string(HTML_TEMPLATE, users=users)

@app.route('/generate_sso_link')
def generate_sso_link():
    user_id = request.args.get('user_id')
    if not user_id:
        return "user_id is required", 400
        
    # JWT 생성
    now = int(time.time())
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "iat": now,
        "exp": now + 60 * 5  # 5분 유효
    }
    
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    
    # 리플라이봇 지정 IP 경로 생성
    replybot_url = f"http://192.168.75.128:5000/sso?token={token}"
    
    return redirect(replybot_url)

SAMPLE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 답변 연동 샘플</title>
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        h1 { border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; color: #1e293b; }
        .form-group { margin-bottom: 25px; }
        label { display: block; font-weight: bold; margin-bottom: 8px; color: #334155; }
        input[type="text"], textarea { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box; font-family: inherit; font-size: 14px; }
        input[type="text"]:focus, textarea:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
        .btn { background-color: #3b82f6; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; font-weight: bold; transition: background-color 0.2s; }
        .btn:hover { background-color: #2563eb; }
        .btn-ai { background-color: #8b5cf6; margin-bottom: 12px; display: inline-flex; align-items: center; gap: 6px; }
        .btn-ai:hover { background-color: #7c3aed; }
        .btn-back { background-color: #64748b; }
        .btn-back:hover { background-color: #475569; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💬 문의 답변 작성 (타 시스템 연동 샘플)</h1>
        
        <div class="form-group" style="background-color: #f8fafc; padding: 20px; border-radius: 6px; border: 1px solid #e2e8f0;">
            <button class="btn btn-ai" onclick="getAIAnswer()">✨ AI 답변</button>
            <label for="queryInput">질의 (고객 문의내용)</label>
            <input type="text" id="queryInput" placeholder="고객의 문의내용을 입력하세요 (예: 비밀번호를 잊어버렸어요, 어떻게 찾나요?)">
        </div>
        
        <div class="form-group">
            <label for="answerArea">답변 (편집 가능)</label>
            <textarea id="answerArea" rows="12" placeholder="AI 답변 버튼을 클릭하면 여기에 추천 답변이 표시됩니다. 자유롭게 편집할 수 있습니다."></textarea>
        </div>
        
        <div style="text-align: right; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
            <a href="/" class="btn btn-back">목록으로 돌아가기</a>
            <button class="btn" onclick="alert('답변이 등록되었습니다. (샘플)')">답변 등록 완료</button>
        </div>
    </div>

    <script>
        async function getAIAnswer() {
            const query = document.getElementById('queryInput').value;
            if (!query.trim()) {
                alert('질의를 먼저 입력해주세요.');
                document.getElementById('queryInput').focus();
                return;
            }
            
            // 버튼 상태 변경
            const btn = document.querySelector('.btn-ai');
            const originalText = btn.innerHTML;
            btn.innerHTML = '⏳ 답변 생성 중...';
            btn.disabled = true;
            
            // 현재 접근한 호스트의 IP를 기반으로 API 호출 (포트는 5000)
            const hostname = '10.10.10.181';
            const apiUrl = `http://${hostname}:5000/api/ai_answer`;
            
            try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                
                if (response.ok && !data.error) {
                    const categoryId = data.categoryId;
                    const category = data.category;
                    const answer = data.answer;
                    
                    // 지정된 포맷으로 텍스트 에어리어에 설정
                    const formattedAnswer = `카테고리: [${categoryId}] ${category}\\n\\n${answer}`;
                    document.getElementById('answerArea').value = formattedAnswer;
                } else {
                    alert('AI 답변을 가져오는데 실패했습니다: ' + (data.error || '알 수 없는 오류'));
                }
            } catch (error) {
                alert('API 호출 중 오류가 발생했습니다. AI 답변 서버(포트 5000)가 실행 중인지, 외부 접근이 허용되어 있는지 확인해주세요.\\n에러 상세: ' + error.message);
                console.error(error);
            } finally {
                // 버튼 상태 복구
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/sample')
def sample_page():
    return render_template_string(SAMPLE_HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
