import tomllib
# import removed

# read data
filepath = 'config/messages.toml'
with open(filepath, 'rb') as f:
    data = tomllib.load(f)

# dashboard additions
for locale in ['ko', 'en']:
    if 'dashboard' not in data[locale]:
        data[locale]['dashboard'] = {}
        
ko_dash = data['ko']['dashboard']
en_dash = data['en']['dashboard']

ko_dash['nav_feedback'] = "피드백"
en_dash['nav_feedback'] = "Feedback"

# Create new sections for simpler HTML changes
data['ko']['feedback_mgr'] = {
    'title_feedback': '피드백',
    'lbl_start_date': '시작일자',
    'lbl_end_date': '종료일자',
    'lbl_has_feedback': '피드백 여부',
    'opt_all': '전체',
    'opt_fb_yes': '피드백 있음',
    'opt_fb_no': '피드백 없음',
    'lbl_rec_category': '추천 카테고리',
    'lbl_decision': '의사결정',
    'decision_accept': '수용',
    'decision_reject': '반려',
    'decision_hold': '보류',
    'decision_pending': '미결정',
    'lbl_search_query': '검색어 (질의 내용)',
    'ph_search_query': '질의 내용을 검색하세요...',
    'btn_search': '검색',
    'col_req_time': '요청 일시',
    'col_query': '질의 내용',
    'col_rec_category': '추천 카테고리',
    'col_user_id': '사용자 ID',
    'col_feedback': '피드백',
    'col_decision': '의사결정',
    'opt_rows_20': '20행',
    'opt_rows_50': '50행',
    'opt_rows_100': '100행',
    'tab_info': '기본정보',
    'tab_decision': '피드백',
    'msg_select_item': '목록에서 항목을 선택하세요.',
    'lbl_admin_opinion': '관리자 의견',
    'ph_admin_opinion': '의사결정 사유나 추가 작업 필요사항 등을 기록하세요.',
    'lbl_confirm_date': '확인 일시',
    'lbl_manager_id': '관리자 ID',
    'btn_save': '저장',
    'lbl_rank_top3': '추천 랭킹 (Top 3)',
    'lbl_fb_template': '피드백 템플릿',
    'msg_no_fb_registered': '이 질의에 대해 등록된 피드백이 없습니다.',
    'msg_select_decision': '의사결정 종류를 선택하세요.',
    'msg_decision_saved': '의사결정 내용이 성공적으로 저장되었습니다.',
    'msg_decision_save_err': '저장 중 오류가 발생했습니다: ',
    'msg_decision_net_err': '저장 중 네트워크 오류가 발생했습니다.',
    'msg_error_loading': '데이터를 불러오는 중 오류가 발생했습니다.',
    'msg_no_data': '조회된 데이터가 없습니다.'
}

data['en']['feedback_mgr'] = {
    'title_feedback': 'Feedback',
    'lbl_start_date': 'Start Date',
    'lbl_end_date': 'End Date',
    'lbl_has_feedback': 'Has Feedback',
    'opt_all': 'All',
    'opt_fb_yes': 'Yes',
    'opt_fb_no': 'No',
    'lbl_rec_category': 'Rec. Category',
    'lbl_decision': 'Decision',
    'decision_accept': 'Accept',
    'decision_reject': 'Reject',
    'decision_hold': 'Hold',
    'decision_pending': 'Pending',
    'lbl_search_query': 'Search Query',
    'ph_search_query': 'Search query text...',
    'btn_search': 'Search',
    'col_req_time': 'Request Time',
    'col_query': 'Query Formulation',
    'col_rec_category': 'Rec. Category',
    'col_user_id': 'User ID',
    'col_feedback': 'Feedback',
    'col_decision': 'Decision',
    'opt_rows_20': '20 Rows',
    'opt_rows_50': '50 Rows',
    'opt_rows_100': '100 Rows',
    'tab_info': 'Basic Info',
    'tab_decision': 'Feedback',
    'msg_select_item': 'Please select an item from the list.',
    'lbl_admin_opinion': 'Admin Opinion',
    'ph_admin_opinion': 'Enter opinion or required actions...',
    'lbl_confirm_date': 'Confirm Date',
    'lbl_manager_id': 'Manager ID',
    'btn_save': 'Save',
    'lbl_rank_top3': 'Recommended Rank (Top 3)',
    'lbl_fb_template': 'Feedback Template',
    'msg_no_fb_registered': 'No feedback registered for this query.',
    'msg_select_decision': 'Please select a decision type.',
    'msg_decision_saved': 'Decision successfully saved.',
    'msg_decision_save_err': 'Error occurred while saving: ',
    'msg_decision_net_err': 'Network error occurred while saving.',
    'msg_error_loading': 'Error occurred while loading data.',
    'msg_no_data': 'No matching data found.'
}

data['ko']['templates_mgr'] = {
    'title_templates': '템플릿 관리',
    'btn_edit_ans': '답변 수정',
    'lbl_category': '카테고리',
    'lbl_ans_template': '답변 템플릿',
    'ph_search_default': '검색어를 입력하세요...',
    'btn_search': '검색',
    'col_category': '카테고리',
    'col_change_cnt': '변경횟수',
    'btn_info': '정보',
    'btn_history': '이력',
    'msg_select_template': '목록에서 템플릿을 선택하세요.',
    'col_date': '일자',
    'col_changer': '변경자',
    'msg_no_data_short': '데이터 없음',
    'lbl_before_change': '변경 전',
    'lbl_after_change': '변경 후',
    'modal_edit_ans': '답변 수정',
    'lbl_ans_content': '답변 내용',
    'btn_cancel': '취소',
    'btn_save': '저장',
    'msg_masking_err': 'Masking 처리 중 오류가 발생했습니다: ',
    'msg_saved': '저장되었습니다.',
    'msg_err': '오류 발생: ',
    'msg_comm_err': '통신 오류: ',
}

data['en']['templates_mgr'] = {
    'title_templates': 'Template Management',
    'btn_edit_ans': 'Edit Answer',
    'lbl_category': 'Category',
    'lbl_ans_template': 'Answer Template',
    'ph_search_default': 'Enter search text...',
    'btn_search': 'Search',
    'col_category': 'Category',
    'col_change_cnt': 'Changes',
    'btn_info': 'Info',
    'btn_history': 'History',
    'msg_select_template': 'Please select a template from the list.',
    'col_date': 'Date',
    'col_changer': 'Modifier',
    'msg_no_data_short': 'No Data',
    'lbl_before_change': 'Before Change',
    'lbl_after_change': 'After Change',
    'modal_edit_ans': 'Edit Answer',
    'lbl_ans_content': 'Answer Content',
    'btn_cancel': 'Cancel',
    'btn_save': 'Save',
    'msg_masking_err': 'Error during masking process: ',
    'msg_saved': 'Saved successfully.',
    'msg_err': 'Error occurred: ',
    'msg_comm_err': 'Communication error: ',
}

data['ko']['login_page'] = {
    'title_set_pw': '비밀번호 설정',
    'desc_set_pw': '초기 비밀번호를 설정해주세요.',
    'label_userid': '사용자 ID',
    'label_name': '이름',
    'label_password': '비밀번호',
    'label_password_confirm': '비밀번호 확인',
    'btn_save_pw': '저장',
    'register_title': '사용자 등록',
    'register_desc': '새로운 관리자 계정을 생성합니다.',
    'placeholder_id': '사번 또는 ID',
    'placeholder_name': '이름',
    'placeholder_email': '이메일 주소',
    'placeholder_password': '비밀번호 설정',
    'placeholder_password_confirm': '비밀번호 확인',
    'btn_signup_submit': '등록하기',
    'btn_cancel': '취소'
}

data['en']['login_page'] = {
    'title_set_pw': 'Set Password',
    'desc_set_pw': 'Please set your initial password.',
    'label_userid': 'User ID',
    'label_name': 'Name',
    'label_password': 'Password',
    'label_password_confirm': 'Confirm Password',
    'btn_save_pw': 'Save',
    'register_title': 'Register User',
    'register_desc': 'Create a new admin account.',
    'placeholder_id': 'Employee ID or User ID',
    'placeholder_name': 'Name',
    'placeholder_email': 'Email Address',
    'placeholder_password': 'Set Password',
    'placeholder_password_confirm': 'Confirm Password',
    'btn_signup_submit': 'Register',
    'btn_cancel': 'Cancel'
}

data['ko']['error_pages'] = {
    'title_error': '오류 - 템플릿 서버',
    'title_server_error': '서버 오류',
    'lbl_error_detail': '오류 내용:',
    'msg_contact_admin': '서버 관리자에게 문의하거나 잠시 후 다시 시도해주세요.',
    'btn_go_main': '메인으로 돌아가기',
    'btn_dashboard': '대시보드'
}

data['en']['error_pages'] = {
    'title_error': 'Error - Template Server',
    'title_server_error': 'Server Error',
    'lbl_error_detail': 'Error Detail:',
    'msg_contact_admin': 'Please contact the server administrator or try again later.',
    'btn_go_main': 'Go back to Main',
    'btn_dashboard': 'Dashboard'
}

# The target file shouldn't be overridden using tomli_w if we don't have it, we can write manually or generate string
def dump_toml(data):
    lines = []
    for lang, sections in data.items():
        for section, keys in sections.items():
            lines.append(f'[{lang}.{section}]')
            for k, v in keys.items():
                if isinstance(v, str):
                    # basic escaping
                    v_esc = v.replace('\"', '\\\"').replace('\n', '\\n')
                    lines.append(f'{k} = \"{v_esc}\"')
            lines.append('')
    return '\n'.join(lines)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(dump_toml(data))

print('Updated TOML.')
