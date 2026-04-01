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
    config_path = 'config/config.toml'
    if os.path.exists(config_path):
        try:
             with open(config_path, 'rb') as f:
                conf = tomllib.load(f)
                if conf:
                    current_theme = conf.get('server', {}).get('theme', 'mono')
        except:
            pass
            
    return render_template('dashboard.html', all_messages=all_messages, current_theme=current_theme, current_user=user_info)

@dashboard_bp.route('/api/stats')
def get_stats():
    db_logger = current_app.config.get('DB_LOGGER')
    if not db_logger:
        return jsonify({"success": False, "error": "DB Logger not initialized"})
    
    stats = db_logger.get_dashboard_stats()
    template_map = get_template_map()
    return jsonify({"success": True, "stats": stats, "template_map": template_map})

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
