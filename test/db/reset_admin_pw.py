from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

from auth_system.auth_core import AuthManager
import tomllib

def reset_admin_pw():
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
        # Reset Admin Password to 'Nexus!234'
        admin = auth._get_user_info('admin')
        if admin:
            print(f"Resetting password for {admin['id']} to 'Nexus!234'...")
            auth.reset_password('admin', 'Nexus!234')
            print("✅ Admin password reset successfully.")
            
            # Ensure unlocked
            auth._reset_fail_count(session, admin['id'])
            session.commit()
            print("✅ Admin unlocked.")
        else:
            print("❌ User 'admin' not found.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    reset_admin_pw()
