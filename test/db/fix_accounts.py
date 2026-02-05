from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

from auth_system.auth_core import AuthManager
import tomllib

def fix_data():
    config_path = os.path.join(root_dir, 'config/config.toml')
    if not os.path.exists(config_path):
        print("config.toml not found")
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
    session = Session()

    auth = AuthManager(Session)
    
    try:
        print("Checking accounts...")
        
        # 1. Unlock Admin
        # Check current status
        admin = auth._get_user_info('admin')
        if admin:
            print(f"Admin Status: Locked={admin['is_locked']}, Fails={admin['failed_login_count']}")
            if admin['is_locked'] or admin['failed_login_count'] > 0:
                print("Unlocking admin...")
                session.execute(text("UPDATE users SET is_locked=0, failed_login_count=0, locked_until=NULL WHERE id=:idu"), {'idu': admin['id']})
                print("Admin unlocked.")
        
        # 2. Fix Nexus Password
        nexus = auth._get_user_info('nexus')
        if nexus:
            print(f"Nexus Status: Hash starts with {nexus['password_hash'][:10] if nexus['password_hash'] else 'None'}")
            
            # If not Argon2 hash (doesn't start with $argon2), re-hash
            if not nexus['password_hash'] or not nexus['password_hash'].startswith('$argon2'):
                print("Re-hashing Nexus password (Nexus!234)...")
                if auth.hasher:
                    hashed = auth.hasher.hash("Nexus!234")
                    session.execute(text("UPDATE users SET password_hash=:h WHERE id=:idu"), {"h": hashed, "idu": nexus['id']})
                    print("Nexus password updated.")
                else:
                    print("⚠️ Argon2 hasher not available! Cannot fix password.")
            else:
                print("Nexus password seems already hashed.")
        else:
            print("Nexus user not found via 'nexus' (ID).")

        session.commit()
        print("✅ Account fix process completed.")

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_data()
