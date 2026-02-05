import pymysql

def test(user, password):
    print(f"Testing {user} with '{password}'...")
    try:
        conn = pymysql.connect(host='127.0.0.1', user=user, password=password)
        print("Success!")
        conn.close()
    except Exception as e:
        print(f"Failed: {e}")

print("--- Root Tests ---")
test('root', '')
test('root', 'root')
test('root', '1234')
