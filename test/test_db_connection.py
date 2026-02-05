import mysql.connector
from mysql.connector import Error

def test_connection(user, password, host='127.0.0.1', database='aidata'):
    print(f"Testing connection for user: {user}...")
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        if connection.is_connected():
            print(f"SUCCESS: Connected to database '{database}' as user '{user}'")
            db_info = connection.get_server_info()
            print("MySQL Server version:", db_info)
            connection.close()
            return True
    except Error as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    # 1. Try Config Credentials
    print("--- Attempt 1: Config Credentials ---")
    if not test_connection('aidata', 'nexus!234'):
        # 2. Try root / no password
        print("\n--- Attempt 2: root / no password ---")
        if not test_connection('root', ''):
            # 3. Try root / root
            print("\n--- Attempt 3: root / root ---")
            if not test_connection('root', 'root'):
                print("\nAll attempts failed.")
