
import mysql.connector

def create_table():
    config = {
        'user': 'aidata',
        'password': 'nexus!234',
        'host': '127.0.0.1',
        'port': 3306,
        'database': 'aidata'
    }

    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
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
        
        cursor.execute(sql)
        conn.commit()
        print("Table 'template_logs' created successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_table()
