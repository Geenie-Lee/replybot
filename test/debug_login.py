import sys
import os

# 부모 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth_system.auth_core import AuthManager
import tomllib

def debug_login():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config/config.toml')

    if not os.path.exists(config_path):
        print(f"config.toml not found at {config_path}")
        return

    with open(config_path, 'rb') as f:
        conf = tomllib.load(f)
        db_conf = conf.get('database', {})

    user = db_conf.get('user', 'root')
    pwd = db_conf.get('password', '')
    host = db_conf.get('host', 'localhost')
    port = db_conf.get('port', 3306)
    dbname = db_conf.get('database', 'aidata')
    
    db_uri = f"mysql+mysqlconnector://{user}:{pwd}@{host}:{port}/{dbname}?charset=utf8mb4"
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    
    print("--- Initializing AuthManager ---")
    auth = AuthManager(Session)
    if auth.hasher:
        print("✅ Hasher: Argon2 Available")
    else:
        print("⚠️ Hasher: None (Plaintext Mode)")

    # 1. Test Admin
    print("\n--- Testing 'admin' / 'Nexus!234' ---")
    success, msg, uid = auth.authenticate('admin', 'Nexus!234', '127.0.0.1')
    print(f"Result: {success}")
    print(f"Message: {msg}")
    print(f"User ID: {uid}")
    
    # Check DB Data
    u = auth._get_user_info('admin')
    if u:
        print(f"DB Hash: {u['password_hash']}")
    else:
        print("DB User 'admin' Not Found")

    # 2. Test Nexus
    print("\n--- Testing 'nexus' / 'nexus1234' ---")
    success, msg, uid = auth.authenticate('nexus', 'nexus1234', '127.0.0.1')
    print(f"Result: {success}")
    print(f"Message: {msg}")
    print(f"User ID: {uid}")

    u = auth._get_user_info('nexus')
    if u:
        print(f"DB Hash: {u['password_hash']}")

if __name__ == "__main__":
    debug_login()
