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

# ==============================================================================
# [설정] 테스트 모의 환경 변수 (외부 설정파일 영향 없이 독립적으로 테스트 가능하도록 명시)
# ==============================================================================
REPLYBOT_AI_API_URL = "http://10.10.10.181:5000/api/ai_answer"
REPLYBOT_SSO_URL = "http://10.10.10.181:5000/sso"

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
    <title>Mock 포탈 및 샘플 시스템</title>
    <style>
        body { font-family: 'Inter', system-ui, -apple-system, sans-serif; background-color: #f1f5f9; color: #1e293b; margin: 0; padding: 20px; box-sizing: border-box; }
        .page-container { display: flex; gap: 20px; width: 100%; max-width: none; margin: 0 auto; box-sizing: border-box; }
        .panel { min-width: 0; background-color: #ffffff; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #DFDDE0; }
        
        h1 { border-bottom: 1px solid #DFDDE0; padding-bottom: 10px; color: #1e293b; margin-top: 0; }
        
        /* Table styles (Left panel) */
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #ffffff; }
        th, td { border: 1px solid #DFDDE0; padding: 12px; text-align: left; color: #475569; }
        th { background-color: #F5F4FA; font-weight: bold; color: #1e293b; }
        .btn { background-color: #014DFF; color: white; padding: 6px 12px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s; display: inline-block; text-align: center; }
        .btn:hover { background-color: #003cd0; box-shadow: 0 0 15px rgba(1, 77, 255, 0.15); }
        .admin-badge { background-color: #ef4444; color: white; padding: 2px 6px; border-radius: 8px; font-size: 11px; }

        /* Form styles (Right panel) */
        .form-group { margin-bottom: 25px; }
        .form-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        label { display: block; font-weight: 500; color: #475569; margin: 0; }
        .btn-clear { background-color: #f1f5f9; color: #475569; padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 4px; cursor: pointer; font-size: 12px; transition: all 0.2s; }
        .btn-clear:hover { background-color: #e2e8f0; color: #1e293b; }
        
        /* Sample Data Table */
        .table-container { margin-bottom: 10px; }
        .sample-table { width: 100%; border-collapse: collapse; font-size: 13px; background-color: #ffffff; margin-bottom: 0; border-top: 2px solid #1e293b; }
        .pagination { display: flex; justify-content: center; gap: 5px; margin-bottom: 25px; }
        .page-btn { padding: 4px 10px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; cursor: pointer; font-size: 12px; color: #475569; }
        .page-btn:hover { background: #f1f5f9; }
        .page-btn.active { background: #014DFF; color: white; border-color: #014DFF; }
        .sample-table th, .sample-table td { padding: 8px 12px; text-align: left; }
        .sample-table th { background-color: #F5F4FA; color: #1e293b; font-weight: 600; border-bottom: 1px solid #DFDDE0; position: sticky; top: 0; z-index: 10; margin: 0; }
        .sample-table th::after { content: ''; position: absolute; left: 0; bottom: 0; width: 100%; border-bottom: 1px solid #DFDDE0; }
        .sample-table td { border-bottom: 1px solid #e2e8f0; margin: 0; } /* lighter border for body rows */
        .sample-table tbody tr { cursor: pointer; transition: background-color 0.2s; }
        .sample-table tbody tr:hover { background-color: #f1f5f9; }
        .sample-table tbody tr:last-child td { border-bottom: none; }
        label { display: block; font-weight: 500; margin-bottom: 8px; color: #475569; }
        input[type="text"], textarea { width: 100%; padding: 12px; border: 1px solid #DFDDE0; border-radius: 8px; box-sizing: border-box; font-family: inherit; font-size: 14px; color: #1e293b; background-color: #ffffff; }
        input[type="text"]:focus, textarea:focus { outline: none; border-color: #014DFF; box-shadow: 0 0 0 2px rgba(1, 77, 255, 0.2); }
        .btn-ai { background-color: #3b82f6; display: inline-flex; align-items: center; gap: 6px; padding: 10px 24px; margin-bottom: 0; }
        .btn-ai:hover { background-color: #2563eb; box-shadow: 0 0 10px rgba(59, 130, 246, 0.2); }
        
        @media (max-width: 1024px) {
            .page-container { flex-direction: column; }
        }
    </style>
    <script>
        function openReplyBot(url) {
            // 새 창(팝업)으로 리플라이봇 풀사이즈 열기
            const w = screen.width;
            const h = screen.height;
            window.open(url, 'replybot', `width=${w},height=${h},top=0,left=0,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=yes`);
        }

        function fillAndSubmit(queryText) {
            const queryInput = document.getElementById('queryInput');
            queryInput.value = queryText;
            document.getElementById('btnAiSubmit').click();
        }

        function clearInput() {
            const queryInput = document.getElementById('queryInput');
            queryInput.value = '';
            document.getElementById('answerArea').value = '';
            queryInput.focus();
        }

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
            btn.innerHTML = '[답변 생성 중...]';
            btn.disabled = true;
            
            // 현재 접근한 호스트의 IP를 기반으로 API 호출 (포트는 5000)
            const apiUrl = '{{ ai_api_url }}';
            
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
                    const formattedAnswer = `[${categoryId}] ${category}\\n\\n${answer}`;
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

        const rowsPerPage = 5;
        let currentPage = 1;
        let sampleRows = [];

        window.onload = function() {
            const tbody = document.getElementById('sampleTableBody');
            if(tbody) {
                sampleRows = Array.from(tbody.querySelectorAll('tr'));
                renderTable();
            }
        };

        function renderTable() {
            const startIndex = (currentPage - 1) * rowsPerPage;
            const endIndex = startIndex + rowsPerPage;
            
            // 기존에 추가된 빈 행들이 있다면 제거
            const tbody = document.getElementById('sampleTableBody');
            const emptyRows = tbody.querySelectorAll('.empty-row');
            emptyRows.forEach(row => row.remove());

            let visibleCount = 0;
            sampleRows.forEach((row, index) => {
                if (index >= startIndex && index < endIndex) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            // 모자란 행 개수만큼 빈 행 추가 (레이아웃 틀어짐 방지)
            if (visibleCount > 0 && visibleCount < rowsPerPage) {
                const emptyCount = rowsPerPage - visibleCount;
                for (let i = 0; i < emptyCount; i++) {
                    const tr = document.createElement('tr');
                    tr.className = 'empty-row';
                    tr.style.cursor = 'default';
                    // 빈 행이라는 것을 사용자가 약간 알수있게 하거나 완전히 티 안나게 처리. 
                    // 여기서는 내용이 없는 td 2개로 기본 높이 유지
                    tr.innerHTML = '<td>&nbsp;</td><td>&nbsp;</td>';
                    tbody.appendChild(tr);
                }
            }
            
            renderPagination();
        }

        function renderPagination() {
            const paginationDiv = document.getElementById('pagination');
            if(!paginationDiv) return;
            paginationDiv.innerHTML = '';
            
            const totalPages = Math.ceil(sampleRows.length / rowsPerPage);
            if(totalPages <= 1) return;
            
            for(let i = 1; i <= totalPages; i++) {
                const btn = document.createElement('button');
                btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
                btn.innerText = i;
                btn.onclick = function() {
                    currentPage = i;
                    renderTable();
                };
                paginationDiv.appendChild(btn);
            }
        }
    </script>
</head>
<body>
    <div class="page-container">
        <!-- 좌측 패널: 사내 포탈 시스템 -->
        <div class="panel" style="flex: 4;">
            <h1>SSO 연동 테스트</h1>
            <p style="margin-bottom: 20px; color: #475569;">현재 AI 리플라이봇에 등록된 사용자 목록입니다.</p>
            
            <table>
                <thead>
                    <tr>
                        <th>사용자 ID</th>
                        <th>이름</th>
                        <th>권한</th>
                        <th>리플라이봇 연동</th>
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
                                통합 인증(SSO)으로 접속
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

        <!-- 우측 패널: 외부 API 연동 샘플 -->
        <div class="panel" style="flex: 6; padding-bottom: 5px;">
            <h1>AI 리플라이봇 API 연동 테스트</h1>
            
            <h3 style="margin-top: 25px; margin-bottom: 10px; font-size: 16px; color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px;">문의 내용(샘플)</h3>
            <div class="table-container">
                <table class="sample-table">
                    <thead>
                        <tr>
                            <th style="width: 30%;">카테고리</th>
                            <th style="width: 70%;">문의 내용</th>
                        </tr>
                    </thead>
                    <tbody id="sampleTableBody">
                        <tr onclick="fillAndSubmit('더블 이용권 구매 어떻게 하나요?')">
                            <td style="width: 30%;">[1] 이용권 구매 방법</td>
                            <td style="width: 70%;">더블 이용권 구매 어떻게 하나요?</td>
                            </tr>
                            <tr onclick="fillAndSubmit('티빙, 웨이브 한꺼번에 있는 거로 이용권 변경 어떻게 해요?')">
                                <td>[14] 이용권 변경</td>
                                <td>티빙, 웨이브 한꺼번에 있는 거로 이용권 변경 어떻게 해요?</td>
                            </tr>
                            <tr onclick="fillAndSubmit('결제 변경하고 싶어요')">
                                <td>[15] 결제 수단 변경 방법</td>
                                <td>결제 변경하고 싶어요</td>
                            </tr>
                            <tr onclick="fillAndSubmit('1년 이용권을 해지하고싶은데 어떻게 진행해요?')">
                                <td>[18] 자동결제 해지 및 구독 취소</td>
                                <td>1년 이용권을 해지하고싶은데 어떻게 진행해요?</td>
                            </tr>
                            <tr onclick="fillAndSubmit('환불 금액은 알겠는데 언제 입금되여?')">
                                <td>[22] 환불_계좌 입금일</td>
                                <td>환불 금액은 알겠는데 언제 입금되여?</td>
                            </tr>
                            <tr onclick="fillAndSubmit('3팩이용권구매로 기존웨이브 이용권을 해지하려하는데.. 환불요청합니다')">
                                <td>[23] 중도환불</td>
                                <td>3팩이용권구매로 기존웨이브 이용권을 해지하려하는데.. 환불요청합니다</td>
                            </tr>
                            <tr onclick="fillAndSubmit('이용권 결제없이 영화 1개 개별구매 방법 알려주세요')">
                                <td>[35] 개별 구매 영화/단건 이용 안내</td>
                                <td>이용권 결제없이 영화 1개 개별구매 방법 알려주세요</td>
                            </tr>
                            <tr onclick="fillAndSubmit('쿠폰 등록 어떻게 하는 건가요?')">
                                <td>[41] 쿠폰전환방법</td>
                                <td>쿠폰 등록 어떻게 하는 건가요?</td>
                            </tr>
                            <tr onclick="fillAndSubmit('sbs 정규방송이 왜 안나오나요?')">
                                <td>[46] SBS 종료</td>
                                <td>sbs 정규방송이 왜 안나오나요?</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div id="pagination" class="pagination"></div>
            
            <div class="form-group" style="background-color: #F5F4FA; padding: 20px; border-radius: 8px; border: 1px solid #DFDDE0;">
                <div class="form-header">
                    <label for="queryInput">문의 내용</label>
                    <button class="btn-clear" onclick="clearInput()">[초기화]</button>
                </div>
                <input type="text" id="queryInput" placeholder="문의 내용을 입력하세요 (예: 비밀번호를 잊어버렸어요, 어떻게 찾나요?)">
                <div style="text-align: center; margin-top: 15px;">
                    <button id="btnAiSubmit" class="btn btn-ai" onclick="getAIAnswer()">AI 답변 요청</button>
                </div>
            </div>
            
            <div class="form-group" style="margin-bottom: 20px;">
                <label for="answerArea">AI 자동 답변</label>
                <textarea id="answerArea" rows="22" placeholder="AI 답변 버튼을 클릭하면 여기에 추천 답변이 표시됩니다. 자유롭게 편집할 수 있습니다."></textarea>
            </div>
        </div>
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
        
    return render_template_string(HTML_TEMPLATE, users=users, ai_api_url=REPLYBOT_AI_API_URL)

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
    replybot_url = f"{REPLYBOT_SSO_URL}?token={token}"
    
    return redirect(replybot_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
