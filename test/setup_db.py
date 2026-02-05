
import mysql.connector
import tomli
import os

def create_table():
    # 1. Try Config Credentials
    config_path = 'config/config.toml'
    db_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'rb') as f:
            conf = tomli.load(f)
            db_config = conf.get('database', {})

    configs_to_try = [
        {
            'user': db_config.get('user', 'aidata'),
            'password': db_config.get('password', ''),
            'host': db_config.get('host', '127.0.0.1'),
            'port': db_config.get('port', 3306),
            'database': db_config.get('database', 'aidata')
        },
        {
            'user': 'root',
            'password': '', # Try empty password
            'host': '127.0.0.1',
            'port': 3306,
            'database': db_config.get('database', 'aidata')
        },
        {
            'user': 'root',
            'password': 'password', # Try common password
            'host': '127.0.0.1',
            'port': 3306,
            'database': db_config.get('database', 'aidata')
        }
    ]

    sql = """
        CREATE TABLE IF NOT EXISTS `template_logs` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `user_id` varchar(20) NOT NULL,
          `log_time` datetime DEFAULT current_timestamp(),
          `category_id` varchar(20) NOT NULL,
          `category` varchar(200) NOT NULL,
          `tobe_answer` text DEFAULT NULL,
          `asis_answer` text DEFAULT NULL,
          PRIMARY KEY (`id`)
        ) engine=innodb default charset=utf8mb4 collate=utf8mb4_unicode_ci;
    """

    conn = None
    for cfg in configs_to_try:
        try:
            print(f"Trying to connect with user: {cfg['user']}...")
            conn = mysql.connector.connect(**cfg)
            print("Connected!")
            
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            print("Table 'template_logs' created successfully.")
            break
        except mysql.connector.Error as err:
            print(f"Failed: {err}")
            conn = None
    
    if conn:
        conn.close()
    else:
        print("Could not create table with any configuration.")

if __name__ == "__main__":
    create_table()
