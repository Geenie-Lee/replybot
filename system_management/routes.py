import os
from flask import render_template, request, jsonify, current_app
from sqlalchemy import create_engine, text
from datetime import datetime, date
from . import system_bp

def _format_datetimes(d):
    """Helper to convert datetime objects to string to prevent GMT offset conversions by JS"""
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(v, date):
            d[k] = v.strftime('%Y-%m-%d')
    return d

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def get_db_engine():
    # Try to get engine from app config if available, or create new one
    # For independent blueprint functioning without circular imports from web_server,
    # we'll read the config directly.
    config_path = os.path.join(current_app.root_path, 'config', 'config.toml')
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
            return create_engine(db_uri)
    return None

@system_bp.route('/users')
def users_page():
    # Helper for messages/i18n if needed, similar to dashboard
    # Load Messages
    messages = {}
    if os.path.exists(os.path.join(current_app.root_path, 'config', 'messages.toml')):
        with open(os.path.join(current_app.root_path, 'config', 'messages.toml'), 'rb') as f:
             messages = tomllib.load(f)

    # Load Server Config (for theme, duck animation)
    server_config = {}
    config_path = os.path.join(current_app.root_path, 'config', 'config.toml')
    if os.path.exists(config_path):
        with open(config_path, 'rb') as f:
            server_config = tomllib.load(f)

    # Get Current User from Session (Reuse AuthManager from app config)
    current_user = None
    auth_manager = current_app.config.get('AUTH_MANAGER')
    token = request.cookies.get('session_token')
    if token and auth_manager:
        sess = auth_manager.get_session(token)
        if sess:
            current_user = dict(sess)

    # Determine current language/theme from cookie or config
    current_lang = request.cookies.get('language', 'ko')
    current_theme = request.cookies.get('theme', server_config.get('server', {}).get('theme', 'mono'))

    return render_template('system/users.html', 
                           all_messages=messages, 
                           messages=messages.get(current_lang, {}), # Pass specific lang messages
                           server_config=server_config,
                           current_user=current_user,
                           current_language=current_lang,
                           current_theme=current_theme)

@system_bp.route('/api/users', methods=['GET', 'POST'])
def api_users_list():
    # POST: Create User
    if request.method == 'POST':
        auth_manager = current_app.config.get('AUTH_MANAGER')
        if not auth_manager:
            return jsonify({'success': False, 'error': 'Auth System not initialized'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        uid = data.get('id')
        name = data.get('username')
        email = data.get('email')
        pw = data.get('password')
        
        if not all([uid, name, email, pw]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        if auth_manager.create_user(uid, name, pw, email):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to create user (ID or Name might vary exists)'}), 400

    # GET: List Users
    engine = get_db_engine()
    if not engine:
        return jsonify({'error': 'DB Configuration Error'}), 500
    
    conn = engine.connect()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        search_cat = request.args.get('category', '')
        search_val = request.args.get('keyword', '')
        
        where_clause = "WHERE 1=1"
        params = {}
        
        if search_val:
            if search_cat == 'id':
                where_clause += " AND id LIKE :val"
            elif search_cat == 'name':
                where_clause += " AND username LIKE :val"
            elif search_cat == 'email':
                where_clause += " AND email LIKE :val"
            else:
                where_clause += " AND (id LIKE :val OR username LIKE :val OR email LIKE :val)"
            params['val'] = f"%{search_val}%"

        # Users table query
        count_sql = text(f"SELECT COUNT(*) FROM users {where_clause}")
        total_count = conn.execute(count_sql, params).scalar()
        
        sql = text(f"""
            SELECT id, username, email, created_at, last_login_at, is_locked, failed_login_count 
            FROM users 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        params['limit'] = per_page
        params['offset'] = offset
        
        result = conn.execute(sql, params).mappings().all()
        # Convert to dict and handle datetime serialization if needed (Flask jsonify handles some, but be careful)
        users_list = []
        for row in result:
            u = _format_datetimes(dict(row))
            users_list.append(u)
        
        return jsonify({
            'data': users_list,
            'total': total_count,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@system_bp.route('/api/users/<user_id>', methods=['GET', 'PUT'])
def api_user_detail(user_id):
    # PUT: Update User
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
             return jsonify({'success': False, 'error': 'No data'}), 400
             
        engine = get_db_engine()
        if not engine: return jsonify({'success': False, 'error': 'DB Error'}), 500
        
        conn = engine.connect()
        try:
            # Prepare update fields
            fields = []
            params = {'uid': user_id}
            
            if 'username' in data:
                fields.append("username = :name")
                params['name'] = data['username']
            if 'email' in data:
                fields.append("email = :email")
                params['email'] = data['email']
            if 'is_locked' in data:
                fields.append("is_locked = :locked")
                params['locked'] = 1 if data['is_locked'] else 0
                if not data['is_locked']:
                     fields.append("failed_login_count = 0")
                     
            if 'password' in data and data['password']:
                auth_manager = current_app.config.get('AUTH_MANAGER')
                pw_hash = data['password']
                if auth_manager and auth_manager.hasher:
                    pw_hash = auth_manager.hasher.hash(data['password'])
                fields.append("password_hash = :hash")
                params['hash'] = pw_hash
            
            if not fields:
                return jsonify({'success': False, 'error': 'No fields to update'})

            sql = text(f"UPDATE users SET {', '.join(fields)} WHERE id = :uid")
            conn.execute(sql, params)
            conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()

    # GET: Get User Detail
    engine = get_db_engine()
    if not engine:
        return jsonify({'error': 'DB Configuration Error'}), 500
        
    conn = engine.connect()
    try:
        sql = text("SELECT id, username, email, created_at, last_login_at, is_locked, failed_login_count, locked_until FROM users WHERE id = :uid")
        result = conn.execute(sql, {'uid': user_id}).mappings().first()
        if result:
            return jsonify(_format_datetimes(dict(result)))
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@system_bp.route('/api/users/<user_id>/logs', methods=['GET'])
def api_user_logs(user_id):
    engine = get_db_engine()
    if not engine:
        return jsonify({'error': 'DB Configuration Error'}), 500
    
    conn = engine.connect()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        count_sql = text("SELECT COUNT(*) FROM replybot_logs WHERE user_id = :uid")
        total_count = conn.execute(count_sql, {'uid': user_id}).scalar()
        
        sql = text("""
            SELECT id, request_time, query_text, predicted_template_id, manual_category, manual_answer,
                   rank1_id, rank2_id, rank3_id, client_ip, processing_time, customer_number
            FROM replybot_logs
            WHERE user_id = :uid
            ORDER BY request_time DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = conn.execute(sql, {'uid': user_id, 'limit': per_page, 'offset': offset}).mappings().all()
        logs = [_format_datetimes(dict(row)) for row in result]
        
        return jsonify({
            'data': logs,
            'total': total_count,
            'page': page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# --------------------------
# Template Management Routes
# --------------------------
import json
import io
import csv
from flask import send_file

import re

def normalize_refund_template(text):
    if text is None:
        return ""
    
    # 1. 일반 항목 금액 치환
    # "결제 금액 : 12,000 원" -> "결제 금액 : 원"
    text = re.sub(r"(결제 금액\s*:\s*)[\d,]+\s*원", r"\1원", text)
    # "결제대행 수수료 : 1,000 원" -> "결제대행 수수료 : 원"
    text = re.sub(r"(결제대행 수수료\s*:\s*)[\d,]+\s*원", r"\1원", text)
    # "환불 가능 금액 : 11,000 원" -> "환불 가능 금액 : 원"
    text = re.sub(r"(환불 가능 금액\s*:\s*)[\d,]+\s*원", r"\1원", text)
    
    # 2. 이용 수수료 항목 정밀 치환
    # "이용 수수료: 5,000 원 (2026-01-01~2026-01-10 /10일)" -> "이용 수수료: 원 (2026-00-00~2026-00-00 /일)"
    # 기존 패턴이 조금 다를 수 있으므로 유연하게 매칭
    # 매칭 대상: 이용 수수료: [숫자,공백]원 ( [날짜]~[날짜] /[숫자]일)
    usage_fee_pattern = r"이용 수수료\s*:\s*[\d,]+\s*원\s*\(\s*\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2}\s*/\s*\d+\s*일\)"
    text = re.sub(usage_fee_pattern, "이용 수수료: 원 (2026-00-00~2026-00-00 /일)", text)
    
    # 3. 입금일 치환
    # "입금일 : 10/29(수)" -> "입금일 : 00/00(요일)"
    # 날짜 형식은 MM/DD(요일) 형태라고 가정
    # 입금일 : [내용] -> 입금일 : 00/00(요일)
    text = re.sub(r"(입금일\s*:\s*)[^\n]+", r"\g<1>00/00(요일)", text)

    return text

@system_bp.route('/api/templates/mask', methods=['POST'])
def api_template_mask():
    data = request.get_json()
    text_content = data.get('text', '')
    masked_text = normalize_refund_template(text_content)
    return jsonify({'masked_text': masked_text})

def get_template_path():
    # Attempt to read config to find template path
    config_path = os.path.join(current_app.root_path, 'config', 'config.toml')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'rb') as f:
                conf = tomllib.load(f)
                files_conf = conf.get('files', {})
                template_file = files_conf.get('templates')
                if template_file:
                    # If the path is relative, join with root_path
                    if not os.path.isabs(template_file):
                         return os.path.join(current_app.root_path, template_file)
                    return template_file
        except Exception as e:
            print(f"Error reading config for templates: {e}")
            
    # Default fallback
    return os.path.join(current_app.root_path, 'model', 'wavve_reply_templates_132.json')

@system_bp.route('/templates')
def templates_page():
    # Load Messages and Config for Layout
    messages = {}
    if os.path.exists(os.path.join(current_app.root_path, 'config', 'messages.toml')):
        with open(os.path.join(current_app.root_path, 'config', 'messages.toml'), 'rb') as f:
             messages = tomllib.load(f)

    server_config = {}
    config_path = os.path.join(current_app.root_path, 'config', 'config.toml')
    if os.path.exists(config_path):
        with open(config_path, 'rb') as f:
            server_config = tomllib.load(f)

    # Load templates
    tpl_path = get_template_path()
    templates_data = []
    if os.path.exists(tpl_path):
        try:
            with open(tpl_path, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
        except Exception as e:
            print(f"Error loading templates: {e}")

    current_lang = request.cookies.get('language', 'ko')
    current_theme = request.cookies.get('theme', server_config.get('server', {}).get('theme', 'mono'))

    return render_template('system/templates_management.html',
                           messages=messages.get(current_lang, {}),
                           server_config=server_config,
                           current_language=current_lang,
                           current_theme=current_theme,
                           templates=templates_data)

@system_bp.route('/api/templates', methods=['GET', 'PUT'])
def api_templates():
    tpl_path = get_template_path()
    
    if request.method == 'GET':
        if os.path.exists(tpl_path):
            with open(tpl_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            # Fetch log counts
            engine = get_db_engine()
            counts = {}
            if engine:
                try:
                    conn = engine.connect()
                    # Ensure table exists (lazy check)
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS `template_logs` (
                          `id` int(11) NOT NULL AUTO_INCREMENT,
                          `user_id` varchar(20) NOT NULL,
                          `log_time` datetime DEFAULT current_timestamp(),
                          `category_id` varchar(20) NOT NULL,
                          `category` varchar(200) NOT NULL,
                          `tobe_answer` text DEFAULT NULL,
                          `asis_answer` text DEFAULT NULL,
                          PRIMARY KEY (`id`)
                        ) engine=innodb default charset=utf8mb4 collate=utf8mb4_unicode_ci;
                    """))
                    conn.commit()

                    # Use a trick to get the last user: GROUP_CONCAT ordering
                    # Note: This might be slightly heavy if logs are huge, but fine for now.
                    # Alternatively, distinct queries or window functions could work.
                    # For simplicity in this env:
                    sql = text("""
                        SELECT category_id, COUNT(*) as cnt,
                        SUBSTRING_INDEX(GROUP_CONCAT(user_id ORDER BY log_time DESC SEPARATOR '||'), '||', 1) as last_user
                        FROM template_logs 
                        GROUP BY category_id
                    """)
                    result = conn.execute(sql).mappings().all()
                    for r in result:
                        counts[str(r['category_id'])] = {
                            'cnt': r['cnt'],
                            'last_user': r['last_user']
                        }
                    conn.close()
                except Exception as e:
                    print(f"DB Error getting counts: {e}")
            
            # Attach counts
            for t in templates:
                data = counts.get(str(t['id']), {})
                t['change_count'] = data.get('cnt', 0)
                t['last_modifier'] = data.get('last_user', 'admin')
                
            return jsonify(templates)
        return jsonify([])

    if request.method == 'PUT':
        data = request.get_json()
        if not data or 'id' not in data:
             return jsonify({'success': False, 'error': 'Missing ID'}), 400
        
        if data['id'] is None:
             return jsonify({'success': False, 'error': 'ID cannot be None'}), 400
             
        try:
            target_id = int(data['id'])
        except (ValueError, TypeError):
             return jsonify({'success': False, 'error': 'Invalid ID format'}), 400
        new_answer = data.get('general_template')

        # Get current user
        # Reuse logic from users_page or middleware?
        # For now, get from session cookie via AuthManager if possible, or simple cookie
        user_id = 'unknown'
        auth_manager = current_app.config.get('AUTH_MANAGER')
        token = request.cookies.get('session_token')
        if token and auth_manager:
            sess = auth_manager.get_session(token)
            if sess:
                # Assuming session dict has 'user_id'
                user_id = sess.get('user_id', 'unknown')

        try:
            with open(tpl_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            updated = False
            asis_answer = ""
            category_name = ""
            
            for t in templates:
                if t['id'] == target_id:
                    asis_answer = t.get('general_template', '')
                    category_name = t.get('inquiry_category', '')
                    t['general_template'] = new_answer
                    
                    # Update change count
                    current_count = t.get('change_count', 0)
                    if current_count is None:
                        current_count = 0
                    t['change_count'] = int(current_count) + 1
                    
                    updated = True
                    break
            
            if updated:
                # 1. Update File
                with open(tpl_path, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=4)
                
                # 2. Insert Log
                engine = get_db_engine()
                if engine:
                    try:
                        conn = engine.connect()
                        sql = text("""
                            INSERT INTO template_logs (user_id, category_id, category, tobe_answer, asis_answer)
                            VALUES (:uid, :cid, :cat, :tobe, :asis)
                        """)
                        conn.execute(sql, {
                            'uid': user_id,
                            'cid': target_id,
                            'cat': category_name,
                            'tobe': new_answer,
                            'asis': asis_answer
                        })
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"DB Log Error: {e}")
                        # Don't fail the request if log fails, but ideally should

                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'ID not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@system_bp.route('/api/templates/<template_id>/logs')
def api_template_logs(template_id):
    engine = get_db_engine()
    if not engine:
        return jsonify([])
    
    try:
        conn = engine.connect()
        sql = text("""
            SELECT id, user_id, log_time, category_id, category, tobe_answer, asis_answer
            FROM template_logs
            WHERE category_id = :cid
            ORDER BY log_time DESC
        """)
        result = conn.execute(sql, {'cid': template_id}).mappings().all()
        logs = [_format_datetimes(dict(r)) for r in result]
        conn.close()
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/api/templates/export')
def api_export_templates():
    export_type = request.args.get('type', 'json')
    tpl_path = get_template_path()
    
    if not os.path.exists(tpl_path):
        return "Template file not found", 404
        
    try:
        with open(tpl_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if export_type == 'json':
            return send_file(
                tpl_path,
                as_attachment=True,
                download_name='templates.json',
                mimetype='application/json'
            )
        elif export_type == 'excel':
            # Excel Export with formatting
            import openpyxl
            from openpyxl.styles import Alignment
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Templates"
            
            # Headers
            headers = ['id', 'inquiry_category', 'general_template', 'description', 'version_type']
            ws.append(headers)
            
            # Data
            for t in data:
                ws.append([
                    t.get('id', ''),
                    t.get('inquiry_category', ''),
                    t.get('general_template', ''),
                    t.get('description', ''),
                    t.get('version_type', '')
                ])
                
            # Column Dimensions
            # id: 5, category: 25, template: 120, desc: 40, version: 15
            ws.column_dimensions['A'].width = 5
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 120
            ws.column_dimensions['D'].width = 40
            ws.column_dimensions['E'].width = 15
            
            # Row Dimensions and Styles
            # Height 150 for data rows
            for row in ws.iter_rows(min_row=2):
                ws.row_dimensions[row[0].row].height = 150
                
                # Wrap text for long fields (C and D) and align top
                for cell in row:
                    cell.alignment = Alignment(vertical='top', wrap_text=True)
            
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            return send_file(
                output,
                as_attachment=True,
                download_name='templates.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        elif export_type == 'csv':
            # Create CSV in memory
            si = io.StringIO()
            cw = csv.writer(si)
            # Headers
            cw.writerow(['id', 'inquiry_category', 'general_template', 'description', 'version_type'])
            for t in data:
                cw.writerow([
                    t.get('id', ''),
                    t.get('inquiry_category', ''),
                    t.get('general_template', ''),
                    t.get('description', ''),
                    t.get('version_type', '')
                ])
            
            output = io.BytesIO()
            output.write(si.getvalue().encode('utf-8-sig')) # BOM for Excel
            output.seek(0)
            
            return send_file(
                output,
                as_attachment=True,
                download_name='templates.csv',
                mimetype='text/csv'
            )
        else:
            return "Unsupported type", 400
            
    except Exception as e:
        return str(e), 500

# --------------------------
# Feedback Management Routes
# --------------------------

@system_bp.route('/feedback')
def feedback_page():
    # Load Messages and Config for Layout
    messages = {}
    if os.path.exists(os.path.join(current_app.root_path, 'config', 'messages.toml')):
        with open(os.path.join(current_app.root_path, 'config', 'messages.toml'), 'rb') as f:
             messages = tomllib.load(f)

    server_config = {}
    config_path = os.path.join(current_app.root_path, 'config', 'config.toml')
    if os.path.exists(config_path):
        with open(config_path, 'rb') as f:
            server_config = tomllib.load(f)

    current_lang = request.cookies.get('language', 'ko')
    current_theme = request.cookies.get('theme', server_config.get('server', {}).get('theme', 'mono'))

    return render_template('system/feedback_management.html',
                           messages=messages.get(current_lang, {}),
                           server_config=server_config,
                           current_language=current_lang,
                           current_theme=current_theme)

@system_bp.route('/api/feedback/categories', methods=['GET'])
def api_feedback_categories():
    engine = get_db_engine()
    if not engine:
        return jsonify({'error': 'DB Configuration Error'}), 500
    
    conn = engine.connect()
    try:
        sql = text("""
            SELECT DISTINCT predicted_template_id as feedback_category 
            FROM replybot_logs 
            WHERE predicted_template_id IS NOT NULL AND predicted_template_id != ''
            ORDER BY CAST(predicted_template_id AS UNSIGNED) ASC
        """)
        result = conn.execute(sql).fetchall()
        categories = [row[0] for row in result if row[0]]
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@system_bp.route('/api/feedback', methods=['GET'])
def api_feedback_logs():
    engine = get_db_engine()
    if not engine:
        return jsonify({'error': 'DB Configuration Error'}), 500
    
    conn = engine.connect()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        keyword = request.args.get('keyword', '').strip()
        has_feedback = request.args.get('has_feedback', 'all')
        categories_str = request.args.get('categories', '')
        categories_list = [c for c in categories_str.split(',') if c] if categories_str else []
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        manager_decision = request.args.get('manager_decision', 'all')
        
        where_clause = "WHERE 1=1"
        params = {}
        
        if keyword:
            where_clause += " AND query_text LIKE :kw"
            params['kw'] = f"%{keyword}%"
            
        if has_feedback == 'yes':
            where_clause += " AND (manual_category IS NOT NULL OR manual_answer IS NOT NULL)"
        elif has_feedback == 'no':
            where_clause += " AND manual_category IS NULL AND manual_answer IS NULL"

        if categories_list:
            in_placeholders = ', '.join([f':cat_{i}' for i in range(len(categories_list))])
            where_clause += f" AND predicted_template_id IN ({in_placeholders})"
            for i, cat in enumerate(categories_list):
                params[f'cat_{i}'] = cat
                
        if start_date:
            where_clause += " AND DATE(request_time) >= :start_date"
            params['start_date'] = start_date
            
        if end_date:
            where_clause += " AND DATE(request_time) <= :end_date"
            params['end_date'] = end_date
            
        if manager_decision == 'pending':
            where_clause += " AND (manager_decision IS NULL OR manager_decision = '') AND (manual_category IS NOT NULL OR manual_answer IS NOT NULL)"
        elif manager_decision != 'all':
            where_clause += " AND manager_decision = :m_dec"
            params['m_dec'] = manager_decision

        count_sql = text(f"SELECT COUNT(*) FROM replybot_logs {where_clause}")
        total_count = conn.execute(count_sql, params).scalar()
        
        # User requested SQL equivalent
        sql = text(f"""
            SELECT id, 
                   request_time, 
                   query_text as question, 
                   predicted_template_id as category_id, 
                   client_ip as user_id, 
                   user_id as actual_user_id, 
                   rank1_id as no1_class_category_id, 
                   rank2_id as no2_class_category_id, 
                   rank3_id as no3_class_category_id, 
                   manual_category as feedback_category, 
                   manual_answer as feedback_answer,
                   manager_id,
                   confirm_date,
                   manager_decision,
                   manager_opinion
            FROM replybot_logs
            {where_clause}
            ORDER BY request_time DESC
            LIMIT :limit OFFSET :offset
        """)
        params['limit'] = per_page
        params['offset'] = offset
        
        result = conn.execute(sql, params).mappings().all()
        logs = [_format_datetimes(dict(row)) for row in result]
        
        return jsonify({
            'data': logs,
            'total': total_count,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@system_bp.route('/api/feedback/decision', methods=['POST'])
def api_feedback_decision():
    auth_manager = current_app.config.get('AUTH_MANAGER')
    if not auth_manager:
        return jsonify({'success': False, 'error': 'Auth System not initialized'}), 500
    
    # Get user who made the decision
    token = request.cookies.get('session_token')
    user_id = 'system'
    if token and auth_manager:
        sess = auth_manager.get_session(token)
        if sess:
            user_id = sess.get('user_id', 'system')

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
        
    log_id = data.get('log_id')
    decision_type = data.get('type')  # 'accept', 'reject', 'hold'
    decision_note = data.get('note', '')
    
    if not log_id or not decision_type:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
    engine = get_db_engine()
    if not engine:
        return jsonify({'error': 'DB Configuration Error'}), 500
        
    conn = engine.connect()
    try:
        # Create feedback_decisions table if it doesn't exist
        create_table_sql = text("""
            CREATE TABLE IF NOT EXISTS feedback_decisions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                log_id INT NOT NULL,
                decision_type VARCHAR(20) NOT NULL,
                decision_note TEXT,
                decision_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX (log_id)
            )
        """)
        conn.execute(create_table_sql)
        
        # Insert the decision
        insert_sql = text("""
            INSERT INTO feedback_decisions (log_id, decision_type, decision_note, decision_by)
            VALUES (:log_id, :type, :note, :user_id)
        """)
        conn.execute(insert_sql, {
            'log_id': log_id,
            'type': decision_type,
            'note': decision_note,
            'user_id': user_id
        })
        
        # Update replybot_logs table with the manager's decision
        update_logs_sql = text("""
            UPDATE replybot_logs
            SET manager_id = :user_id,
                confirm_date = CURRENT_TIMESTAMP(),
                manager_decision = :type,
                manager_opinion = :note
            WHERE id = :log_id
        """)
        conn.execute(update_logs_sql, {
            'log_id': log_id,
            'type': decision_type,
            'note': decision_note,
            'user_id': user_id
        })
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Decision saved successfully'})
        
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()
