import mysql.connector
from mysql.connector import Error

# MySQL 연결 함수
def get_db():
    try:
        connection = mysql.connector.connect(
            host="project-db-campus.smhrd.com",
            port=3312,
            user="mp_24K_DCX13_p3_2",
            password="smhrd2",
            database="stock_project"
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None
