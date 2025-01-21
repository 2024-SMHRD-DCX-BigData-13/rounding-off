import mysql.connector
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
import threading
import sys
import time
import datetime


def clean_price(raw_price):
    """
    키움 OpenAPI에서 반환된 현재가 데이터를 정리합니다.
    :param raw_price: 부호가 포함된 현재가 (문자열)
    :return: 부호를 제거한 정수 값
    """
    try:
        return abs(int(raw_price))  # 부호 제거 및 정수 변환
    except ValueError:
        print(f"[ERROR] Invalid price format: {raw_price}")
        return 0


def clean_old_data():
    """
    이전 날짜 데이터를 삭제합니다.
    """
    try:
        connection = mysql.connector.connect(
            host="project-db-cgi.smhrd.com",
            user="mp_24K_DCX13_p3_2",
            password="smhrd2",
            database="mp_24K_DCX13_p3_2",
            port=3307
        )
        cursor = connection.cursor()

        # 현재 날짜 가져오기
        today = datetime.datetime.now().date()

        # 이전 날짜 데이터 삭제
        query = """
        DELETE FROM realtime_stocks
        WHERE DATE(create_at) < %s
        """
        cursor.execute(query, (today,))
        connection.commit()

        print(f"[DEBUG] Old data cleaned: {cursor.rowcount} rows deleted")
    except mysql.connector.Error as err:
        print(f"[ERROR] Database error during cleanup: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.real_data = {}

        # 이벤트 연결
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveRealData.connect(self._on_receive_real_data)

    def login(self):
        print("[DEBUG] Attempting to log in...")
        self.dynamicCall("CommConnect()")

    def _on_event_connect(self, err_code):
        if err_code == 0:
            print("[DEBUG] Login successful!")
            self.connected = True
        else:
            print(f"[ERROR] Login failed with error code: {err_code}")

    def request_real_data(self, screen_no, codes, fid_list):
        result = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, codes, fid_list, "0")
        if result == 0:
            print(f"[DEBUG] Real-time data registration successful for codes: {codes}")
        else:
            print("[ERROR] Real-time data registration failed.")
        print(f"[DEBUG] Real-time request - ScreenNo: {screen_no}, Codes: {codes}, FIDs: {fid_list}")

    def _on_receive_real_data(self, code, real_type, data):
        if real_type == "주식체결":
            raw_price = self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            current_price = clean_price(raw_price)

            # 데이터가 유효한지 확인
            if current_price > 0:
                print(f"[DEBUG] Valid Data Received - Code: {code}, Price: {current_price}")
                self.real_data[code] = {"current_price": current_price}
            else:
                print(f"[DEBUG] Invalid Data Skipped - Code: {code}, RawPrice: {raw_price}")


def fetch_stock_codes_from_db():
    """
    MySQL에서 종목 코드를 가져옵니다.
    :return: 세미콜론으로 구분된 종목 코드 문자열
    """
    try:
        connection = mysql.connector.connect(
            host="project-db-cgi.smhrd.com",
            user="mp_24K_DCX13_p3_2",
            password="smhrd2",
            database="mp_24K_DCX13_p3_2",
            port=3307
        )
        cursor = connection.cursor()
        cursor.execute("SELECT stock_idx FROM stocks LIMIT 20")  # 최대 20개 종목
        rows = cursor.fetchall()
        stock_codes = ";".join(row[0] for row in rows)
        print(f"[DEBUG] Loaded stock codes from DB: {stock_codes}")
        return stock_codes
    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        return ""
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def save_to_db(data):
    """
    MySQL에 데이터를 저장.
    :param data: 실시간 데이터 딕셔너리 (종목코드별 데이터)
    """
    if not data:
        print("[DEBUG] No data to save to DB.")
        return

    try:
        connection = mysql.connector.connect(
            host="project-db-cgi.smhrd.com",
            user="mp_24K_DCX13_p3_2",
            password="smhrd2",
            database="mp_24K_DCX13_p3_2",
            port=3307
        )
        cursor = connection.cursor()

        # 데이터 삽입 쿼리
        query = """
        INSERT INTO realtime_stocks (stock_idx, current_price, create_at)
        VALUES (%s, %s, NOW())
        """
        values = [(code, info["current_price"]) for code, info in data.items()]
        cursor.executemany(query, values)  # 배치 삽입
        connection.commit()

        print(f"[DEBUG] Data saved to DB: {len(values)} records")
    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def periodic_save(kiwoom, interval=5):
    """
    5초마다 실시간 데이터를 DB에 저장.
    """
    while True:
        time.sleep(interval)
        if kiwoom.real_data:
            save_to_db(kiwoom.real_data)
        else:
            print("[DEBUG] No real-time data available to save.")


def start_kiwoom():
    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI()
    kiwoom.login()

    while not kiwoom.connected:
        app.processEvents()

    stock_codes = fetch_stock_codes_from_db()
    if not stock_codes:
        print("[ERROR] Failed to fetch stock codes from DB.")
        return

    screen_no = "1000"
    fid_list = "10"  # 현재가만 요청
    kiwoom.request_real_data(screen_no, stock_codes, fid_list)

    print("[DEBUG] KiwoomManager started.")

    # 주기적으로 DB에 저장하는 스레드 실행
    save_thread = threading.Thread(target=periodic_save, args=(kiwoom,), daemon=True)
    save_thread.start()

    # 하루가 끝나면 데이터를 정리하는 스레드 실행
    cleaner_thread = threading.Thread(target=clean_old_data, daemon=True)
    cleaner_thread.start()

    app.exec_()


if __name__ == "__main__":
    start_kiwoom()
