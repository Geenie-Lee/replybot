import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. feedback_management.html
fb_repl = [
    ('<title>피드백</title>', '<title>{{ messages.dashboard.nav_feedback }}</title>'),
    ('<span>피드백</span>', '<span>{{ messages.dashboard.nav_feedback }}</span>'),
    ('<h2 style="font-size:1.2rem; font-weight:700;">피드백 관리</h2>', '<h2 style="font-size:1.2rem; font-weight:700;">{{ messages.feedback_mgr.title_feedback }}</h2>'),
    ('<h2 style="font-size:1.2rem; font-weight:700;">피드백</h2>', '<h2 style="font-size:1.2rem; font-weight:700;">{{ messages.feedback_mgr.title_feedback }}</h2>'),
    ('시작일자</label>', '{{ messages.feedback_mgr.lbl_start_date }}</label>'),
    ('종료일자</label>', '{{ messages.feedback_mgr.lbl_end_date }}</label>'),
    ('피드백 여부</label>', '{{ messages.feedback_mgr.lbl_has_feedback }}</label>'),
    ('추천 카테고리</label>', '{{ messages.feedback_mgr.lbl_rec_category }}</label>'),
    ('의사결정</label>', '{{ messages.feedback_mgr.lbl_decision }}</label>'),
    ('검색어 (질의\n                            내용)</label>', '{{ messages.feedback_mgr.lbl_search_query }}</label>'),
    ('검색어 (질의\r\n                            내용)</label>', '{{ messages.feedback_mgr.lbl_search_query }}</label>'),
    ('검색어 (질의 내용)</label>', '{{ messages.feedback_mgr.lbl_search_query }}</label>'),
    ('검색어 (질의\n                                내용)</label>','{{ messages.feedback_mgr.lbl_search_query }}</label>'),
    ('>전체</option>', '>{{ messages.feedback_mgr.opt_all }}</option>'),
    ('>피드백 있음</option>', '>{{ messages.feedback_mgr.opt_fb_yes }}</option>'),
    ('>피드백 없음</option>', '>{{ messages.feedback_mgr.opt_fb_no }}</option>'),
    ('>수용</option>', '>{{ messages.feedback_mgr.decision_accept }}</option>'),
    ('>반려</option>', '>{{ messages.feedback_mgr.decision_reject }}</option>'),
    ('>보류</option>', '>{{ messages.feedback_mgr.decision_hold }}</option>'),
    ('>미결정</option>', '>{{ messages.feedback_mgr.decision_pending }}</option>'),
    ('placeholder="질의 내용을 검색하세요..."', 'placeholder="{{ messages.feedback_mgr.ph_search_query }}"'),
    ('<i class="fas fa-search"></i> 검색', '<i class="fas fa-search"></i> {{ messages.feedback_mgr.btn_search }}'),
    ('<th>요청 일시</th>', '<th>{{ messages.feedback_mgr.col_req_time }}</th>'),
    ('<th>질의 내용</th>', '<th>{{ messages.feedback_mgr.col_query }}</th>'),
    ('<th>추천 카테고리</th>', '<th>{{ messages.feedback_mgr.col_rec_category }}</th>'),
    ('<th>사용자 ID</th>', '<th>{{ messages.feedback_mgr.col_user_id }}</th>'),
    ('<th>피드백</th>', '<th>{{ messages.feedback_mgr.col_feedback }}</th>'),
    ('<th>의사결정</th>', '<th>{{ messages.feedback_mgr.col_decision }}</th>'),
    ('요청 일시</th>', '{{ messages.feedback_mgr.col_req_time }}</th>'),
    ('추천 카테고리</th>', '{{ messages.feedback_mgr.col_rec_category }}</th>'),
    ('사용자 ID</th>', '{{ messages.feedback_mgr.col_user_id }}</th>'),
    ('피드백</th>', '{{ messages.feedback_mgr.col_feedback }}</th>'),
    ('의사결정</th>', '{{ messages.feedback_mgr.col_decision }}</th>'),
    ('>20행</option>', '>{{ messages.feedback_mgr.opt_rows_20 }}</option>'),
    ('>50행</option>', '>{{ messages.feedback_mgr.opt_rows_50 }}</option>'),
    ('>100행</option>', '>{{ messages.feedback_mgr.opt_rows_100 }}</option>'),
    ('기본정보</button>', '{{ messages.feedback_mgr.tab_info }}</button>'),
    ('피드백</button>', '{{ messages.feedback_mgr.tab_decision }}</button>'),
    ('목록에서 항목을 선택하세요.', '{{ messages.feedback_mgr.msg_select_item }}'),
    ('관리자 의견</label>', '{{ messages.feedback_mgr.lbl_admin_opinion }}</label>'),
    ('선택하세요...</option>', '>{{ messages.dashboard.ph_search | default("...") }}</option>'), # fallback or just match it
    ('placeholder="의사결정 사유나 추가 작업 필요사항 등을 기록하세요."', 'placeholder="{{ messages.feedback_mgr.ph_admin_opinion }}"'),
    ('<strong>확인 일시:</strong>', '<strong>{{ messages.feedback_mgr.lbl_confirm_date }}:</strong>'),
    ('<strong>관리자 ID:</strong>', '<strong>{{ messages.feedback_mgr.lbl_manager_id }}:</strong>'),
    ('onclick="saveDecision()">저장</button>', 'onclick="saveDecision()">{{ messages.feedback_mgr.btn_save }}</button>'),
    ('<span class="detail-label">요청 일시</span>', '<span class="detail-label">{{ messages.feedback_mgr.col_req_time }}</span>'),
    ('<span class="detail-label">질의 내용</span>', '<span class="detail-label">{{ messages.feedback_mgr.col_query }}</span>'),
    ('<span class="detail-label">추천 템플릿</span>', '<span class="detail-label">{{ messages.dashboard.nav_templates }}</span>'), 
    ('<span class="detail-label">추천 랭킹 (Top 3)</span>', '<span class="detail-label">{{ messages.feedback_mgr.lbl_rank_top3 }}</span>'),
    ('<span class="detail-label">피드백 템플릿</span>', '<span class="detail-label">{{ messages.feedback_mgr.lbl_fb_template }}</span>'),
    ('이 질의에 대해 등록된 피드백이 없습니다.', '{{ messages.feedback_mgr.msg_no_fb_registered }}'),
    ("alert('의사결정 종류를 선택하세요.');", "alert('{{ messages.feedback_mgr.msg_select_decision }}');"),
    ("alert('의사결정 내용이 성공적으로 저장되었습니다.');", "alert('{{ messages.feedback_mgr.msg_decision_saved }}');"),
    ("alert('저장 중 오류가 발생했습니다: '", "alert('{{ messages.feedback_mgr.msg_decision_save_err }}'"),
    ("|| '알 수 없는 오류'", "|| '알 수 없는 오류'"),
    ("alert('저장 중 네트워크 오류가 발생했습니다.');", "alert('{{ messages.feedback_mgr.msg_decision_net_err }}');"),
    ('데이터를 불러오는 중 오류가 발생했습니다.', '{{ messages.feedback_mgr.msg_error_loading }}'),
    ('조회된 데이터가 없습니다.', '{{ messages.feedback_mgr.msg_no_data }}'),
    ('<span class="detail-label">추천 카테고리</span>', '<span class="detail-label">{{ messages.feedback_mgr.col_rec_category }}</span>')
]
replace_in_file('templates/system/feedback_management.html', fb_repl)

# 2. templates_management.html
tp_repl = [
    ('<title>템플릿 관리</title>', '<title>{{ messages.templates_mgr.title_templates }}</title>'),
    ('<span>템플릿 관리</span>', '<span>{{ messages.templates_mgr.title_templates }}</span>'),
    ('<h2 style="font-size:1.2rem; font-weight:700;">템플릿 관리</h2>', '<h2 style="font-size:1.2rem; font-weight:700;">{{ messages.templates_mgr.title_templates }}</h2>'),
    ('<i class="fas fa-edit"></i> 답변 수정', '<i class="fas fa-edit"></i> {{ messages.templates_mgr.btn_edit_ans }}'),
    ('카테고리</label>', '{{ messages.templates_mgr.lbl_category }}</label>'),
    ('답변 템플릿</label>', '{{ messages.templates_mgr.lbl_ans_template }}</label>'),
    ('placeholder="검색어를 입력하세요..."', 'placeholder="{{ messages.templates_mgr.ph_search_default }}"'),
    ('<i class="fas fa-search"></i> 검색', '<i class="fas fa-search"></i> {{ messages.templates_mgr.btn_search }}'),
    ('<th>카테고리 <span', '<th>{{ messages.templates_mgr.col_category }} <span'),
    ('<th>변경횟수</th>', '<th style="width: 80px;">{{ messages.templates_mgr.col_change_cnt }}</th>'),
    ('정보</button>', '{{ messages.templates_mgr.btn_info }}</button>'),
    ('이력</button>', '{{ messages.templates_mgr.btn_history }}</button>'),
    ('목록에서 템플릿을 선택하세요.', '{{ messages.templates_mgr.msg_select_template }}'),
    ('>일자</th>', '>{{ messages.templates_mgr.col_date }}</th>'),
    ('<th>카테고리</th>', '<th style="padding:0.5rem;">{{ messages.templates_mgr.col_category }}</th>'),
    ('>변경자</th>', '>{{ messages.templates_mgr.col_changer }}</th>'),
    ('데이터 없음</td>', '{{ messages.templates_mgr.msg_no_data_short }}</td>'),
    ('변경 전', '{{ messages.templates_mgr.lbl_before_change }}'),
    ('변경 후', '{{ messages.templates_mgr.lbl_after_change }}'),
    ('<div class="modal-header">답변 수정</div>', '<div class="modal-header">{{ messages.templates_mgr.modal_edit_ans }}</div>'),
    ('답변 내용', '{{ messages.templates_mgr.lbl_ans_content }}'),
    ('>취소</button>', '>{{ messages.templates_mgr.btn_cancel }}</button>'),
    ('class="btn btn-primary">저장</button>', 'class="btn btn-primary">{{ messages.templates_mgr.btn_save }}</button>'),
    ("alert('Masking 처리 중 오류가 발생했습니다: '", "alert('{{ messages.templates_mgr.msg_masking_err }}'"),
    ("alert('저장되었습니다.');", "alert('{{ messages.templates_mgr.msg_saved }}');"),
    ("alert('오류 발생: '", "alert('{{ messages.templates_mgr.msg_err }}'"),
    ("alert('통신 오류: '", "alert('{{ messages.templates_mgr.msg_comm_err }}'"),
    ('오류 발생</td>', '{{ messages.templates_mgr.msg_no_data_short }}</td>'),
    ('조회된 데이터가 없습니다.', '{{ messages.feedback_mgr.msg_no_data }}'),
    ('<span class="detail-label">카테고리</span>', '<span class="detail-label">{{ messages.templates_mgr.lbl_category }}</span>'),
    ('<span class="detail-label">답변 템플릿</span>', '<span class="detail-label">{{ messages.templates_mgr.lbl_ans_template }}</span>'),
    ('<span class="detail-label">답변 내용</span>', '<span class="detail-label">{{ messages.templates_mgr.lbl_ans_content }}</span>'),
]
replace_in_file('templates/system/templates_management.html', tp_repl)

# 3. users.html has `피드백` and `피드백 관리` already replaced by {{messages.dashboard.nav_feedback}} but we used "피드백".
usr_repl = [
    ('<span>피드백</span>', '<span>{{ messages.dashboard.nav_feedback }}</span>')
]
replace_in_file('templates/system/users.html', usr_repl)

# 4. login.html
login_repl = [
    ('<h3 class="modal-title">비밀번호 설정</h3>', '<h3 class="modal-title">{{ messages.login_page.title_set_pw }}</h3>'),
    ('<p class="modal-desc">초기 비밀번호를 설정해주세요.</p>', '<p class="modal-desc">{{ messages.login_page.desc_set_pw }}</p>'),
    ('<label>사용자 ID</label>', '<label>{{ messages.login_page.label_userid }}</label>'),
    ('<label>이름</label>', '<label>{{ messages.login_page.label_name }}</label>'),
    ('<label>비밀번호</label>', '<label>{{ messages.login_page.label_password }}</label>'),
    ('<label>비밀번호 확인</label>', '<label>{{ messages.login_page.label_password_confirm }}</label>'),
    ('style="margin-top:1rem;">저장</button>', 'style="margin-top:1rem;">{{ messages.login_page.btn_save_pw }}</button>'),
    ('<h3 class="modal-title" data-i18n="login.register_title">사용자 등록</h3>', '<h3 class="modal-title" data-i18n="login.register_title">{{ messages.login_page.register_title }}</h3>'),
    ('<p class="modal-desc" data-i18n="login.register_desc">새로운 관리자 계정을 생성합니다.</p>', '<p class="modal-desc" data-i18n="login.register_desc">{{ messages.login_page.register_desc }}</p>'),
    ('<label data-i18n="login.label_userid">사용자 ID</label>', '<label data-i18n="login.label_userid">{{ messages.login_page.label_userid }}</label>'),
    ('<label data-i18n="login.label_name">이름</label>', '<label data-i18n="login.label_name">{{ messages.login_page.label_name }}</label>'),
    ('<label data-i18n="login.label_email">이메일</label>', '<label data-i18n="login.label_email">{{ messages.login_page.label_email }}</label>'),
    ('<label data-i18n="login.label_password">비밀번호</label>', '<label data-i18n="login.label_password">{{ messages.login_page.label_password }}</label>'),
    ('<label data-i18n="login.label_password_confirm">비밀번호 확인</label>', '<label data-i18n="login.label_password_confirm">{{ messages.login_page.label_password_confirm }}</label>'),
    ('data-i18n="login.btn_signup_submit">등록하기</button>', 'data-i18n="login.btn_signup_submit">{{ messages.login_page.btn_signup_submit }}</button>'),
    ('data-i18n="login.btn_cancel">취소</button>', 'data-i18n="login.btn_cancel">{{ messages.login_page.btn_cancel }}</button>'),
]
replace_in_file('templates/login.html', login_repl)

# 5. dashboard.html
db_repl = [
    ('<span>피드백</span>', '<span>{{ messages.dashboard.nav_feedback|default(all_messages["ko"]["dashboard"]["nav_feedback"]) }}</span>'),
    ('피드백 관리', '{{ messages.dashboard.nav_feedback }}')
]
replace_in_file('dashboard/templates/dashboard.html', db_repl)

# 6. error.html
err_repl = [
    ('<title>오류 - 신세계라이브쇼핑 템플릿 서버</title>', '<title>{{ messages.common.title_error | default(messages.error_pages.title_error)|default("Error") }}</title>'),
    ('<h1>서버 오류</h1>', '<h1>{{ messages.error_pages.title_server_error }}</h1>'),
    ('<strong>오류 내용:</strong>', '<strong>{{ messages.error_pages.lbl_error_detail }}</strong>'),
    ('<p>서버 관리자에게 문의하거나 잠시 후 다시 시도해주세요.</p>', '<p>{{ messages.error_pages.msg_contact_admin }}</p>'),
    ('메인으로 돌아가기</a>', '{{ messages.error_pages.btn_go_main }}</a>')
]
replace_in_file('templates/error.html', err_repl)

# 7. index.html - Check if any remaining hardcoded strings. We can use python re to see if any missed.
idx_repl = [
    ('>대시보드<', '>{{ messages.common.btn_dashboard | default(messages.error_pages.btn_dashboard)|default("Dashboard") }}<')
]
replace_in_file('templates/index.html', idx_repl)

print("HTML replacer completed.")
