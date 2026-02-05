from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

from auth_system.auth_core import AuthManager
import tomllib

def set_nexus_password():
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
        # Update Nexus Password to 'nexus1234'
        nexus = auth._get_user_info('nexus')
        if nexus:
            print(f"Updating password for {nexus['id']} (Name: {nexus['username']}) to 'nexus1234'...")
            auth.reset_password(nexus['username'], 'nexus1234')
            print("✅ Password updated successfully.")
        else:
            print("❌ User 'nexus' not found.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    set_nexus_password()
