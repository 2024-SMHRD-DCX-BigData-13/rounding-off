import sys
import time
import datetime
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
import mysql.connector

def clean_price(raw_price):
    try:
        return abs(int(raw_price))
    except ValueError:
        print(f"[ERROR] Invalid price format: {raw_price}")
        return 0

class KiwoomAPI(QAxWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.real_data = {}
        self.data = []
        self.current_stock = None
        self.stock_list = []
        self.db_connection = db_connection

        # 이벤트 연결
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_trdata)
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

    def fetch_stock_list(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT stock_idx, stock_name FROM stocks")
            self.stock_list = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"[ERROR] Database error: {err}")

    def process_next_stock(self):
        if not self.stock_list:
            print("[INFO] All stocks processed.")
            return

        self.current_stock = self.stock_list.pop(0)
        stock_code, stock_name = self.current_stock
        print(f"[INFO] Requesting data for {stock_name} ({stock_code})")
        self.request_stock_data(stock_code)

    def request_stock_data(self, stock_code):
        self.data = []
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=180)
        formatted_date = end_date.strftime("%Y%m%d")

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.dynamicCall("SetInputValue(QString, QString)", "기준일자", formatted_date)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")

    def _on_receive_trdata(self, screen_no, rqname, trcode, recordname, prev_next):
        if rqname == "주식일봉차트조회":
            data_count = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(data_count):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()
                open_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()
                close_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()

                self.data.append({
                    "date": date,
                    "open": int(open_price),
                    "high": int(high_price),
                    "low": int(low_price),
                    "close": int(close_price),
                    "volume": int(volume)
                })

            self.save_to_db()
            time.sleep(1)
            self.process_next_stock()

    def save_to_db(self):
        if not self.current_stock:
            return

        stock_code, stock_name = self.current_stock
        cursor = self.db_connection.cursor()

        # 기존 데이터 삭제
        cursor.execute("DELETE FROM stock_datas WHERE stock_idx = %s", (stock_code,))

        for record in self.data:
            cursor.execute(
                """
                INSERT INTO stock_datas (stock_idx, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (stock_code, record["date"], record["open"], record["high"], record["low"], record["close"], record["volume"])
            )

        self.db_connection.commit()
        print(f"[INFO] Data for {stock_name} saved to DB.")

    def request_real_data(self, screen_no, codes, fid_list):
        result = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, codes, fid_list, "0")
        if result == 0:
            print(f"[DEBUG] Real-time data registration successful for codes: {codes}")
        else:
            print("[ERROR] Real-time data registration failed.")

    def _on_receive_real_data(self, code, real_type, data):
        if real_type == "주식체결":
            raw_price = self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            current_price = clean_price(raw_price)
            if current_price > 0:
                self.real_data[code] = {"current_price": current_price}
                print(f"[DEBUG] Real-time Data Received - Code: {code}, Price: {current_price}")


def periodic_save_real_data(kiwoom, interval=5):
    """
    실시간 데이터를 주기적으로 저장하는 함수.
    실시간 데이터가 없으면 데이터베이스 작업을 건너뜀.
    """
    while True:
        time.sleep(interval)  # 주기적으로 실행 (기본: 5초)

        # 실시간 데이터가 없으면 건너뛰기
        if not kiwoom.real_data:
            print("[INFO] No real-time data available. Skipping database save.")
            continue

        try:
            connection = kiwoom.db_connection
            cursor = connection.cursor()

            query = """
            INSERT INTO realtime_stocks (stock_idx, current_price, create_at)
            VALUES (%s, %s, NOW())
            """
            # 데이터베이스에 삽입할 값 준비
            values = [(code, info["current_price"]) for code, info in kiwoom.real_data.items()]
            
            # 데이터 삽입 실행
            cursor.executemany(query, values)
            connection.commit()

            print(f"[DEBUG] Real-time data saved: {len(values)} records")
        except mysql.connector.Error as err:
            print(f"[ERROR] Database error: {err}")


def periodic_save_daily_data(kiwoom):
    while True:
        now = datetime.datetime.now()
        if now.hour == 17 and now.minute == 0:  # 매일 오후 5시에 실행
            kiwoom.fetch_stock_list()
            kiwoom.process_next_stock()
        time.sleep(60)  # 1분마다 체크


def main():
    db_connection = mysql.connector.connect(
        host="project-db-cgi.smhrd.com",
        user="mp_24K_DCX13_p3_2",
        password="smhrd2",
        database="mp_24K_DCX13_p3_2",
        port=3307
    )

    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI(db_connection)
    kiwoom.login()

    while not kiwoom.connected:
        app.processEvents()

    # 실시간 데이터 요청
    kiwoom.fetch_stock_list()
    stock_codes = ";".join(code for code, _ in kiwoom.stock_list)
    kiwoom.request_real_data("1000", stock_codes, "10")

    # 실시간 데이터 저장 스레드
    save_real_thread = threading.Thread(target=periodic_save_real_data, args=(kiwoom,), daemon=True)
    save_real_thread.start()

    # 일봉 데이터 저장 스레드
    save_daily_thread = threading.Thread(target=periodic_save_daily_data, args=(kiwoom,), daemon=True)
    save_daily_thread.start()

    app.exec_()


if __name__ == "__main__":
    main()
