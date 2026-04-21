import json
import os
from flask import Blueprint, render_template, jsonify, current_app

try:
    import tomllib
except ImportError:
    import tomli as tomllib

dashboard_bp = Blueprint('dashboard', __name__, 
    template_folder='templates',
    static_folder='static'
)

def get_all_messages():
    msg_file = 'config/messages.toml'
    if os.path.exists(msg_file):
        try:
            with open(msg_file, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"Error loading messages: {e}")
            return {}
    return {}

def get_template_map():
    try:
        config_path = 'config/config.toml'
        template_path = 'model/reply_templates_80.json' # default fallback

        if os.path.exists(config_path):
            with open(config_path, 'rb') as f:
                conf = tomllib.load(f)
                if conf and 'files' in conf and 'templates' in conf['files']:
                    template_path = conf['files']['templates']
        
        # Ensure absolute path or correct relative path
        if not os.path.isabs(template_path):
            # Assuming relative to workspace root (where web_server.py is usually run)
            # But let's check existence directly first
            if not os.path.exists(template_path):
                # Try finding it relative to current file? No, usually CWD is root
                pass

        if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    # Template file is a list of dicts: [{"id": 1, "inquiry_category": "...", ...}, ...]
                    return {str(t['id']): t.get('inquiry_category', '') for t in templates}
    except Exception as e:
        print(f"Error loading template map: {e}")
    return {}

@dashboard_bp.route('/')
def index():
    from flask import request, redirect, url_for, make_response
    
    # Check Admin Access
    token = request.cookies.get('session_token')
    auth_manager = current_app.config.get('AUTH_MANAGER')
    
    if not token or not auth_manager:
        return redirect('/login')
        
    sess = auth_manager.get_session(token)
    if not sess:
        return redirect('/login')
        
    user_info = auth_manager._get_user_info(sess.get('user_id'))
    if not user_info or user_info.get('admin_yn') != 'Y':
        return make_response("접근 권한이 없습니다. (관리자만 접근 가능합니다.)", 403)

    all_messages = get_all_messages()
    
    # Get Current Theme
    current_theme = 'mono'
    logs_visible = True
    config_path = 'config/config.toml'
    if os.path.exists(config_path):
        try:
             with open(config_path, 'rb') as f:
                conf = tomllib.load(f)
                if conf:
                    current_theme = conf.get('server', {}).get('theme', 'mono')
                    logs_cfg = conf.get('dashboard', {}).get('logs_area', {}).get('visible', 'on')
                    # check if false, 'off', '0'
                    if str(logs_cfg).lower() in ['off', 'false', '0']:
                        logs_visible = False
        except:
            pass
            
    return render_template('dashboard.html', all_messages=all_messages, current_theme=current_theme, current_user=user_info, logs_visible=logs_visible, embed_mode=False)

# ──────────────────────────────────────────────────────────────────────────────
# 공개 대시보드 렌더 헬퍼 (web_server.py의 /replybot/dashboard 라우트에서 호출)
# ──────────────────────────────────────────────────────────────────────────────
def render_public_dashboard():
    """인증 없이 접근 가능한 공개 대시보드 렌더링 (좌측 메뉴 없음)"""
    from flask import request

    # ── Access Log 기록 ──
    db_logger = current_app.config.get('DB_LOGGER')
    if db_logger:
        try:
            db_logger.log_access(
                client_ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                referer=request.headers.get('Referer'),
                access_path=request.path,
                query_string=request.query_string.decode('utf-8', errors='ignore')
            )
        except Exception as e:
            print(f"Access log error: {e}")

    all_messages = get_all_messages()

    current_theme = 'mono'
    logs_visible = True
    config_path = 'config/config.toml'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'rb') as f:
                conf = tomllib.load(f)
                if conf:
                    current_theme = conf.get('server', {}).get('theme', 'mono')
                    logs_cfg = conf.get('dashboard', {}).get('logs_area', {}).get('visible', 'on')
                    if str(logs_cfg).lower() in ['off', 'false', '0']:
                        logs_visible = False
        except:
            pass

    return render_template(
        'dashboard.html',
        all_messages=all_messages,
        current_theme=current_theme,
        current_user=None,
        logs_visible=logs_visible,
        embed_mode=True          # 사이드바 숨김 플래그
    )

@dashboard_bp.route('/api/stats')
def get_stats():
    from flask import request
    db_logger = current_app.config.get('DB_LOGGER')
    if not db_logger:
        return jsonify({"success": False, "error": "DB Logger not initialized"})
    
    user_limit = request.args.get('user_limit', 10, type=int)
    relation_limit = request.args.get('relation_limit', 5, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_hour = request.args.get('start_hour')
    end_hour = request.args.get('end_hour')
    date_unit = request.args.get('date_unit', 'day')
    weekdays = request.args.get('weekdays')
    
    stats = db_logger.get_dashboard_stats(
        user_limit=user_limit, 
        relation_limit=relation_limit,
        start_date=start_date,
        end_date=end_date,
        start_hour=start_hour,
        end_hour=end_hour,
        date_unit=date_unit,
        weekdays=weekdays
    )
    template_map = get_template_map()
    return jsonify({"success": True, "stats": stats, "template_map": template_map})

@dashboard_bp.route('/api/export-excel')
def export_excel():
    from flask import request, send_file
    import io
    import pandas as pd
    from datetime import datetime

    db_logger = current_app.config.get('DB_LOGGER')
    if not db_logger:
        return jsonify({"success": False, "error": "DB Logger not initialized"})
    
    user_limit = request.args.get('user_limit', 10, type=int)
    relation_limit = request.args.get('relation_limit', 5, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    start_hour = request.args.get('start_hour')
    end_hour = request.args.get('end_hour')
    date_unit = request.args.get('date_unit', 'day')
    weekdays = request.args.get('weekdays')
    
    stats = db_logger.get_dashboard_stats(
        user_limit=user_limit, 
        relation_limit=relation_limit,
        start_date=start_date,
        end_date=end_date,
        start_hour=start_hour,
        end_hour=end_hour,
        date_unit=date_unit,
        weekdays=weekdays
    )
    template_map = get_template_map()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 시트1. Summary
        summary = stats.get('summary', {})
        total_queries = summary.get('total', 0)
        feedback_rate = stats.get('feedback_rate', 0)
        total_templates = len(template_map.keys()) if template_map else 0
        
        summary_df = pd.DataFrame([
             {"총 템플릿 수": total_templates, "총 질의 수": total_queries, "피드백 비율(%)": round(feedback_rate, 2)}
        ])
        
        top_templates = stats.get('top_templates', [])
        top_template_data = []
        for t in top_templates:
            tid = t.get('predicted_template_id')
            cat = template_map.get(str(tid), '')
            top_template_data.append({"템플릿 ID": tid, "카테고리": cat, "사용 횟수": t.get('count')})
        top_template_df = pd.DataFrame(top_template_data)
        
        summary_df.to_excel(writer, sheet_name='KPI', index=False, startrow=0)
        top_template_df.to_excel(writer, sheet_name='KPI', index=False, startrow=3)
        worksheet1 = writer.sheets['KPI']
        worksheet1.cell(row=3, column=1, value='상위 5개 템플릿')
        
        # 시트2. 일간 질의 추이
        daily_trend = stats.get('daily_trend', [])
        daily_data = []
        for t in daily_trend:
            d = t.get('date')
            if d:
                daily_data.append({"일자": str(d), "질의 수": t.get('count')})
        daily_df = pd.DataFrame(daily_data)
        daily_df.to_excel(writer, sheet_name='일간추이', index=False, startrow=0)
        
        # 시트3. 사용자 활동 지표
        user_stats = stats.get('user_stats', [])
        user_data = []
        for u in user_stats:
            count = u.get('count', 0)
            ratio = round((count / total_queries) * 100, 2) if total_queries > 0 else 0
            user_data.append({
                "사용자 ID": u.get('user_id'), 
                "질의 수": count, 
                "비중(%)": ratio
            })
        user_df = pd.DataFrame(user_data)
        user_df.to_excel(writer, sheet_name='사용자활동', index=False, startrow=0)
        
        # 시트4. 사용자-템플릿 관계
        user_template_stats = stats.get('user_template_stats', [])
        ut_data = []
        for ut in user_template_stats:
            tid = ut.get('predicted_template_id')
            cat = template_map.get(str(tid), '')
            ut_data.append({
                "사용자 ID": ut.get('user_id'),
                "템플릿 ID": tid,
                "카테고리": cat,
                "사용 횟수": ut.get('usage_count')
            })
        ut_df = pd.DataFrame(ut_data)
        ut_df.to_excel(writer, sheet_name='사용자템플릿', index=False, startrow=0)

        # 시트5. 일별 사용자 질의 수
        daily_user_stats = stats.get('daily_user_stats', [])
        du_data = []
        for du in daily_user_stats:
            du_data.append({
                "일자": str(du.get('date')) if du.get('date') else '',
                "사용자 ID": du.get('user_id'),
                "질의 수": du.get('count')
            })
        du_df = pd.DataFrame(du_data)
        du_df.to_excel(writer, sheet_name='사용자일간추이', index=False, startrow=0)

        # 모든 시트의 열 폭을 20으로 설정
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for col in worksheet.columns:
                column_letter = col[0].column_letter
                worksheet.column_dimensions[column_letter].width = 20

    output.seek(0)
    filename = f"dashboard_report_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@dashboard_bp.route('/api/logs')
def get_logs():
    from flask import request
    db_logger = current_app.config.get('DB_LOGGER')
    if not db_logger:
        return jsonify({"success": False, "error": "DB Logger not initialized"})

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    # Filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    predicted_id = request.args.get('predicted_id')
    user_id = request.args.get('user_id')
    feedback_status = request.args.get('feedback_status')
    query_text = request.args.get('query_text')

    data = db_logger.get_logs(page, page_size, start_date, end_date, predicted_id, user_id, feedback_status, query_text)
    return jsonify({"success": True, "data": data})

@dashboard_bp.route('/api/export-logs-excel')
def export_logs_excel():
    from flask import request, send_file
    import io
    import pandas as pd
    from datetime import datetime
    
    db_logger = current_app.config.get('DB_LOGGER')
    if not db_logger:
        return jsonify({"success": False, "error": "DB Logger not initialized"})

    # Filters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    predicted_id = request.args.get('predicted_id')
    user_id = request.args.get('user_id')
    feedback_status = request.args.get('feedback_status')
    query_text = request.args.get('query_text')
    category_filter = request.args.get('category')
    manager_decision = request.args.get('manager_decision')

    # 페이징 없이 대량 조회를 위한 설정
    data = db_logger.get_logs(1, 100000, start_date, end_date, predicted_id, user_id, feedback_status, query_text)
    logs = data.get('logs', [])

    export_data = []
    template_map = get_template_map()
    
    for log in logs:
        if manager_decision and manager_decision != 'all':
            if log.get('manager_decision') != manager_decision:
                continue
                
        conf_val = ''
        if log.get('confidence') is not None and str(log.get('confidence')).strip() != '':
            try:
                conf_val = round(float(log.get('confidence')) * 100, 2)
            except ValueError:
                conf_val = ''
                
        tid = log.get('predicted_template_id')
        cat_name = template_map.get(str(tid), '') if tid else ''
        rec_category = f"[{tid}] {cat_name}" if tid else '-'
        
        has_fb = bool(log.get('manual_answer') or log.get('manual_category') or log.get('feedback_answer') or log.get('feedback_category'))
        
        if category_filter and category_filter != 'all':
            m_cat = str(log.get('manual_category') or log.get('feedback_category') or '')
            if category_filter not in rec_category and category_filter not in m_cat:
                continue
                
        fb_status = '있음' if has_fb else '없음'
        
        decision_raw = log.get('manager_decision')
        if decision_raw == 'accept':
            decision_str = '수용'
        elif decision_raw == 'reject':
            decision_str = '반려'
        elif decision_raw == 'hold':
            decision_str = '보류'
        else:
            decision_str = '-'
            
        fb_template = '-'
        if has_fb:
            m_cat = log.get('manual_category') or log.get('feedback_category')
            if m_cat:
                m_str = str(m_cat).strip()
                if m_str.startswith('['):
                    fb_template = m_str
                else:
                    m_cat_name = template_map.get(m_str, '')
                    if m_cat_name:
                        fb_template = f"[{m_str}] {m_cat_name}"
                    else:
                        fb_template = m_str
                        
        user_id_str = log.get('actual_user_id') or log.get('user_id') or '-'

        export_data.append({
            "요청 일시": log.get('request_time'),
            "질의 내용": log.get('query_text'),
            "추천 카테고리": rec_category,
            "사용자ID": user_id_str,
            "피드백": fb_status,
            "의사결정": decision_str,
            "피드백 템플릿": fb_template
        })

    df = pd.DataFrame(export_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='피드백')
        
        worksheet = writer.sheets['피드백']
        for col in worksheet.columns:
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = 20

    output.seek(0)
    filename = f"feedback_logs_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@dashboard_bp.route('/api/filters')
def get_api_filters():
    db_logger = current_app.config.get('DB_LOGGER')
    if not db_logger:
        return jsonify({"success": False, "error": "DB Logger not initialized"})
    
    data = db_logger.get_filter_options()
    return jsonify({"success": True, "data": data})

@dashboard_bp.route('/api/health')
def health_check():
    from flask import request
    
    logged_in = False
    
    # Check Session
    token = request.cookies.get('session_token')
    auth_manager = current_app.config.get('AUTH_MANAGER')
    
    if token and auth_manager:
        sess = auth_manager.get_session(token)
        if sess:
            logged_in = True
    
    # If auth_manager is missing, fallback to assuming logged out or just ok
    # But since we enforced 'session check', if auth_manager is missing (not init), we might assume logged_in=False
    
    return jsonify({"success": True, "status": "ok", "logged_in": logged_in})

def get_full_templates():
    try:
        config_path = 'config/config.toml'
        template_path = 'model/reply_templates_80.json' 
        if os.path.exists(config_path):
            with open(config_path, 'rb') as f:
                conf = tomllib.load(f)
                if conf and 'files' in conf and 'templates' in conf['files']:
                    template_path = conf['files']['templates']
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
                # Return relevant fields
                results = []
                for t in templates:
                    category = t.get('inquiry_category', t.get('title', ''))
                    # version = t.get('version_type', '')
                    # base = t.get('base_category', '')
                    
                    # User Request: Use inquiry_category directly
                    display_category = category
                        
                    results.append({
                        "id": t['id'], 
                        "category": display_category, 
                        "answer": t.get('consultation_guide', '') or t.get('answer', '') or t.get('template_text', '') or t.get('content', '') or t.get('general_template', '')
                    })
                return results
    except Exception as e:
        print(f"Error loading full templates: {e}")
    return []

@dashboard_bp.route('/api/templates')
def api_templates():
    return jsonify({"success": True, "templates": get_full_templates()})

@dashboard_bp.route('/api/save_feedback', methods=['POST'])
def save_feedback():
    from flask import request
    db_logger = current_app.config.get('DB_LOGGER')
    if not db_logger:
        return jsonify({"success": False, "error": "DB Logger error"})
    
    data = request.json
    log_id = data.get('log_id')
    template_id = data.get('template_id')
    manual_answer = data.get('manual_answer')
    user_id = data.get('user_id') 
    
    if not log_id:
        return jsonify({"success": False, "error": "Missing log_id"})

    # Derive category name from ID if possible
    manual_category = ""
    if template_id:
        templates = get_full_templates()
        for t in templates:
            if str(t['id']) == str(template_id):
                manual_category = t['category']
                break
    
    # Fallback or override
    if not manual_category and data.get('manual_category'):
        manual_category = data.get('manual_category')

    # Revert to using update_manual_answer (only updates logs table)
    # Assuming update_manual_answer signature: (log_id, manual_answer, manual_category, user_id)
    success = db_logger.update_manual_answer(log_id, manual_answer, manual_category, user_id)
    return jsonify({"success": success})
