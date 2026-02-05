from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth_system.auth_core import AuthManager
import tomllib
import os

def debug_nexus():
    if not os.path.exists('config/config.toml'):
        print("config.toml not found")
        return

    with open('config/config.toml', 'rb') as f:
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
    
    auth = AuthManager(Session)

    # 2. Test Nexus
    print("\n--- Testing 'nexus' / 'nexus1234' ---")
    success, msg, uid = auth.authenticate('nexus', 'nexus1234', '127.0.0.1')
    print(f"Result: {success}")
    print(f"Message: {msg}")
    print(f"User ID: {uid}")

if __name__ == "__main__":
    debug_nexus()
