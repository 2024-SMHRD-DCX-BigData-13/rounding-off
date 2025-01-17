# import mysql.connector
# from mysql.connector import Error

# def create_connection():
#     """ MySQL 데이터베이스 연결을 설정하는 함수 """
#     try:
#         connection = mysql.connector.connect(
#             host='project-db-campus.smhrd.com',         # MySQL 서버 주소 (기본 localhost)
#             port=3312,                # MySQL 서버 포트 (기본 3306, 다른 포트인 경우 변경)
#             database='mp_24K_DCX13_p3_2', # 연결할 데이터베이스 이름
#             user='mp_24K_DCX13_p3_2',     # MySQL 사용자명
#             password='smhrd2'  # MySQL 비밀번호
#         )
#         if connection.is_connected():
#             print("MySQL 데이터베이스에 성공적으로 연결되었습니다.")
#             return connection
#     except Error as e:
#         print(f"데이터베이스 연결 실패: {e}")
#         return None

# def close_connection(connection):
#     """ 데이터베이스 연결을 종료하는 함수 """
#     if connection and connection.is_connected():
#         connection.close()
#         print("MySQL 연결이 종료되었습니다.")


import mysql.connector
from mysql.connector import Error

def create_connection():
    """ MySQL 데이터베이스 연결을 설정하는 함수 """
    try:
        connection = mysql.connector.connect(
            host='localhost',         # MySQL 서버 주소 (기본 localhost)
            port=3306,                # MySQL 서버 포트 (기본 3306, 다른 포트인 경우 변경)
            database='books', # 연결할 데이터베이스 이름
            user='com',     # MySQL 사용자명
            password='com01'  # MySQL 비밀번호
        )
        if connection.is_connected():
            print("MySQL 데이터베이스에 성공적으로 연결되었습니다.")
            return connection
    except Error as e:
        print(f"데이터베이스 연결 실패: {e}")
        return None

def close_connection(connection):
    """ 데이터베이스 연결을 종료하는 함수 """
    if connection and connection.is_connected():
        connection.close()
        print("MySQL 연결이 종료되었습니다.")

