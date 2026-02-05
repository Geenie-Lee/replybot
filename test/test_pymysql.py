import pymysql

def test(user, password, host='127.0.0.1', db='aidata'):
    print(f"Testing {user}...")
    try:
        conn = pymysql.connect(host=host, user=user, password=password, database=db)
        print("Success!")
        conn.close()
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

print("--- Attempt 1: aidata ---")
test('aidata', 'nexus!234')

print("\n--- Attempt 2: root (no pass) ---")
test('root', '')

print("\n--- Attempt 3: root (root) ---")
test('root', 'root')
