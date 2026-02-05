
import mysql.connector
import datetime
import os

try:
    import tomllib
except ImportError:
    import tomli as tomllib

class DBLogger:
    def __init__(self, config_path='config/config.toml'):
        self.config = self._load_config(config_path)
        self.db_config = self.config.get('database', {})
        self._ensure_table_exists()

    def _load_config(self, path):
        try:
            abs_path = os.path.abspath(path)
            # print(f"📂 설정 파일 로드 경로: {abs_path}")
            with open(path, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"❌ 설정 파일({path}) 로드 실패: {e}")
            return {}

    def _get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.db_config.get('host', 'localhost'),
                user=self.db_config.get('user', 'root'),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', 'aidata'),
                port=self.db_config.get('port', 3306),
                charset='utf8mb4',
                connection_timeout=5,
                auth_plugin='mysql_native_password'
            )
        except mysql.connector.Error as e:
            print(f"❌ DB 연결 실패: {e} (Host: {self.db_config.get('host')})")
            raise e

    def _ensure_table_exists(self):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS replybot_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            customer_number VARCHAR(50),
            consultation_type VARCHAR(100),
            query_text TEXT,
            predicted_template_id INT,
            rank1_id INT,
            rank2_id INT,
            rank3_id INT,
            confidence FLOAT,
            processing_time FLOAT,
            client_ip VARCHAR(50)
        )
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            
            # 컬럼 추가 (테이블이 이미 존재할 경우)
            try:
                cursor.execute("ALTER TABLE replybot_logs ADD COLUMN rank1_id INT")
                print("✅ rank1_id 컬럼 추가됨")
            except:
                pass
            try:
                cursor.execute("ALTER TABLE replybot_logs ADD COLUMN rank2_id INT")
                print("✅ rank2_id 컬럼 추가됨")
            except:
                pass
            try:
                cursor.execute("ALTER TABLE replybot_logs ADD COLUMN rank3_id INT")
                print("✅ rank3_id 컬럼 추가됨")
            except:
                pass
            
            # 피드백(수동 답변) 컬럼 추가
            try:
                cursor.execute("ALTER TABLE replybot_logs ADD COLUMN manual_answer TEXT")
                print("✅ manual_answer 컬럼 추가됨")
            except:
                pass

            try:
                cursor.execute("ALTER TABLE replybot_logs ADD COLUMN manual_category VARCHAR(100)")
                print("✅ manual_category 컬럼 추가됨")
            except:
                pass

            try:
                cursor.execute("ALTER TABLE replybot_logs ADD COLUMN user_id VARCHAR(50)")
                print("✅ user_id 컬럼 추가됨")
            except:
                pass
                
            cursor.close()
            conn.close()
            print("✅ 로그 테이블(replybot_logs) 확인/생성 완료")
            


        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")



    def log_query(self, customer_number, consultation_type, query_text, predicted_template_id, confidence, processing_time, client_ip, top_template_ids=[], user_id=None):
        sql = """
        INSERT INTO replybot_logs (
            customer_number, consultation_type, query_text, 
            predicted_template_id, rank1_id, rank2_id, rank3_id,
            confidence, processing_time, client_ip, request_time, user_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # 상위 3개 ID 추출
        r1 = top_template_ids[0] if len(top_template_ids) > 0 else None
        r2 = top_template_ids[1] if len(top_template_ids) > 1 else None
        r3 = top_template_ids[2] if len(top_template_ids) > 2 else None
        
        # predicted_template_id가 없으면 rank1_id를 사용
        if predicted_template_id is None:
            predicted_template_id = r1

        inserted_id = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (
                customer_number, 
                consultation_type, 
                query_text, 
                predicted_template_id,
                r1, r2, r3,
                confidence, 
                processing_time, 
                client_ip,
                datetime.datetime.now(),
                user_id
            ))
            conn.commit()
            inserted_id = cursor.lastrowid
            cursor.close()
            conn.close()
            # print(f"📝 쿼리 로그 저장 완료: ID {inserted_id}")
            return inserted_id
        except Exception as e:
            print(f"❌ 로그 저장 실패: {e}")
            return None

    def update_manual_answer(self, log_id, manual_answer, manual_category, user_id=None):
        """
        사용자 피드백을 로그 테이블에 업데이트함. (replybot_manual_feedback 테이블 사용 안함)
        """
        update_log_sql = """
            UPDATE replybot_logs 
            SET manual_answer = %s, manual_category = %s, user_id = %s
            WHERE id = %s
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(update_log_sql, (manual_answer, manual_category, user_id, log_id))
            conn.commit()
            updated = cursor.rowcount > 0
            cursor.close()
            conn.close()
            
            if updated:
                print(f"✅ 로그 ID {log_id} 피드백 업데이트 완료")
            return True
        except Exception as e:
            print(f"❌ 피드백 업데이트 실패: {e}")
            return False

    def get_dashboard_stats(self):
        """대시보드 통계 데이터 조회"""
        stats = {
            "summary": {"total": 0, "avg_confidence": 0, "feedback_count": 0, "avg_processing_time": 0},
            "daily_trend": [],
            "top_templates": [],
            "user_stats": [],
            "feedback_rate": 0
        }
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            # 1. 요약 정보
            cursor.execute("""
                SELECT 
                    COUNT(*) as total, 
                    AVG(confidence) as avg_confidence,
                    AVG(processing_time) as avg_processing_time,
                    COUNT(manual_answer) as feedback_count
                FROM replybot_logs
            """)
            summary = cursor.fetchone()
            if summary:
                stats["summary"] = summary
                if summary['total'] > 0:
                    stats["feedback_rate"] = (summary['feedback_count'] / summary['total']) * 100

            # 2. 일별 트렌드 (최근 7일)
            cursor.execute("""
                SELECT 
                    DATE(request_time) as date, 
                    COUNT(*) as count 
                FROM replybot_logs 
                GROUP BY DATE(request_time) 
                ORDER BY date DESC 
                LIMIT 7
            """)
            stats["daily_trend"] = cursor.fetchall()[::-1] # 역순으로 정렬하여 날짜 오름차순

            # 3. 상위 템플릿 사용
            cursor.execute("""
                SELECT 
                    predicted_template_id, 
                    COUNT(*) as count 
                FROM replybot_logs 
                WHERE predicted_template_id IS NOT NULL 
                GROUP BY predicted_template_id 
                ORDER BY count DESC 
                LIMIT 5
            """)
            stats["top_templates"] = cursor.fetchall()

            # 4. 사용자별 통계 (Top 5)
            try:
                cursor.execute("""
                    SELECT 
                        user_id,
                        COUNT(*) as count,
                        AVG(confidence) as avg_conf 
                    FROM replybot_logs 
                    WHERE user_id IS NOT NULL AND user_id != ''
                    GROUP BY user_id 
                    ORDER BY count DESC
                    LIMIT 5
                """)
                stats['user_stats'] = cursor.fetchall()
            except Exception as e:
                print(f"User Stats Error: {e}")

            # 5. 사용자 - 템플릿 상호작용 통계 (Top 5 users only)
            try:
                # Top 5 유저 추출
                top_users = [u['user_id'] for u in stats['user_stats']]
                
                if top_users:
                    # tuple(top_users)가 1개일 때 (x,) 형태가 되어야 함.
                    # python mysql connector handles tuple/list in IN clause nicely usually via %s and manual formatting or distinct placeholders
                    # Here simplest is to string format for the IN clause since valid user_ids are expected safe or simple strings
                    format_strings = ','.join(['%s'] * len(top_users))
                    
                    sql = f"""
                        SELECT 
                            user_id, 
                            predicted_template_id, 
                            COUNT(*) as usage_count 
                        FROM replybot_logs 
                        WHERE user_id IN ({format_strings}) AND predicted_template_id IS NOT NULL
                        GROUP BY user_id, predicted_template_id
                        ORDER BY user_id, usage_count DESC
                    """
                    cursor.execute(sql, tuple(top_users))
                    stats['user_template_stats'] = cursor.fetchall()
                else:
                    stats['user_template_stats'] = []

            except Exception as e:
                print(f"User Template Stats Error: {e}")
            
            cursor.close()
            conn.close()
            return stats
        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")
            return stats

    def get_logs(self, page=1, page_size=20, start_date=None, end_date=None, predicted_id=None, user_id=None, feedback_status=None, query_text=None):
        """로그 데이터 페이징 및 필터 조회"""
        try:
            offset = (page - 1) * page_size
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)

            where_clauses = []
            params = []

            if start_date:
                where_clauses.append("request_time >= %s")
                params.append(f"{start_date} 00:00:00")
            if end_date:
                where_clauses.append("request_time <= %s")
                params.append(f"{end_date} 23:59:59")
            if predicted_id:
                where_clauses.append("predicted_template_id = %s")
                params.append(predicted_id)
            if user_id:
                where_clauses.append("user_id = %s")
                params.append(user_id)
            
            if feedback_status == 'feedback':
                where_clauses.append("manual_answer IS NOT NULL AND manual_answer != ''")
            elif feedback_status == 'none':
                where_clauses.append("(manual_answer IS NULL OR manual_answer = '')")
            
            if query_text:
                where_clauses.append("query_text LIKE %s")
                params.append(f"%{query_text}%")

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            # 전체 개수 조회
            count_sql = f"SELECT COUNT(*) as count FROM replybot_logs {where_sql}"
            cursor.execute(count_sql, tuple(params))
            total_count = cursor.fetchone()['count']

            # 페이징 데이터 조회
            sql = f"""
                SELECT * FROM replybot_logs 
                {where_sql}
                ORDER BY request_time DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, tuple(params + [page_size, offset]))
            logs = cursor.fetchall()
            
            # datetime 객체 변환 (JSON 직렬화를 위해)
            for log in logs:
                if isinstance(log['request_time'], datetime.datetime):
                    log['request_time'] = log['request_time'].strftime('%Y-%m-%d %H:%M:%S')

            cursor.close()
            conn.close()
            
            return {
                "logs": logs,
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 0
            }
        except Exception as e:
            print(f"❌ 로그 조회 실패: {e}")
            return {"logs": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 0}

    def get_filter_options(self):
        """필터용 Distinct 데이터 조회"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT DISTINCT predicted_template_id FROM replybot_logs WHERE predicted_template_id IS NOT NULL ORDER BY predicted_template_id")
            preds = [row['predicted_template_id'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT user_id FROM replybot_logs WHERE user_id IS NOT NULL AND user_id != '' ORDER BY user_id")
            users = [row['user_id'] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            return {"predicted_ids": preds, "user_ids": users}
        except Exception as e:
            print(f"❌ 필터 옵션 조회 실패: {e}")
            return {"predicted_ids": [], "user_ids": []}
