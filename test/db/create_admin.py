from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

from auth_system.auth_core import AuthManager
import tomllib

def create_admin():
    try:
        # Config 로드
        config_path = os.path.join(root_dir, 'config/config.toml')
        if not os.path.exists(config_path):
            print(f"config.toml not found at {config_path}")
            return

        with open(config_path, 'rb') as f:
            conf = tomllib.load(f)
            db_conf = conf.get('database', {})

        # DB 연결
        user = db_conf.get('user', 'root')
        pwd = db_conf.get('password', '')
        host = db_conf.get('host', 'localhost')
        port = db_conf.get('port', 3306)
        dbname = db_conf.get('database', 'aidata')

        print(f"Connecting to {host}:{port}/{dbname} as {user}...")
        
        db_uri = f"mysql+mysqlconnector://{user}:{pwd}@{host}:{port}/{dbname}?charset=utf8mb4"
        engine = create_engine(db_uri)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 0. Initialize Schema
        print("Initializing Database Schema...")
        try:
            schema_path = os.path.join(root_dir, 'auth_system/schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            statements = schema_sql.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt:
                    try:
                        session.execute(text(stmt))
                        session.commit()
                    except Exception as sql_err:
                        # Ignore "database exists" or similar non-fatal DDL errors
                        # print(f"⚠️ SQL Exec Warning: {str(sql_err)[:100]}...") 
                        session.rollback()
                        
            print("✅ Schema applied.")
        except Exception as e:
            print(f"❌ Schema Init Failed: {e}")

        # AuthManager
        auth = AuthManager(Session)
        
        # Check existing
        existing = auth._get_user_info('admin')
        if existing:
            print("✅ 'admin' user already exists.")
            # Optional: Force update password? No, just keep it.
        else:
            # Create admin
            # ID: admin, Username: Administrator, Pass: Nexus!234, Email: admin@replybot.com
            success = auth.create_user(
                user_id='admin',
                username='admin', 
                password='Nexus!234', 
                email='admin@replybot.com'
            )
            if success:
                print("✅ Successfully created 'admin' user.")
                print("   ID: admin")
                print("   PW: Nexus!234")
            else:
                print("❌ Failed to create admin user.")
        
        session.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_admin()
