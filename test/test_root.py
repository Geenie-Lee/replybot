import mysql.connector

try:
    print("Trying root with no password...")
    conn = mysql.connector.connect(host='127.0.0.1', user='root', password='')
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Failed: {e}")

try:
    print("Trying root with password 'root'...")
    conn = mysql.connector.connect(host='127.0.0.1', user='root', password='root')
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Failed: {e}")
