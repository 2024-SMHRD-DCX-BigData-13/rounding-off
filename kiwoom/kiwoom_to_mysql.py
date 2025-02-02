import sys
import time
import datetime
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from mysql.connector import pooling, Error


def clean_price(raw_price):
    try:
        return abs(int(raw_price))
    except ValueError:
        print(f"[ERROR] Invalid price format: {raw_price}")
        return 0


class KiwoomAPI(QAxWidget):
    def __init__(self, db_pool):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.real_data = {}
        self.data = []
        self.current_stock = None
        self.stock_list = []
        self.db_pool = db_pool  # MySQL 연결 풀

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
        """
        MySQL에서 종목 리스트를 가져옵니다.
        """
        try:
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT stock_idx, stock_name FROM stocks")
            self.stock_list = cursor.fetchall()
        except Error as err:
            print(f"[ERROR] Database error: {err}")
        finally:
            cursor.close()
            connection.close()

    def process_next_stock(self):
        """
        다음 종목 데이터를 요청합니다. 모든 종목이 처리되면 종료.
        """
        if not self.stock_list:
            print("[INFO] All stocks processed.")
            return

        self.current_stock = self.stock_list.pop(0)
        stock_code, stock_name = self.current_stock
        print(f"[INFO] Requesting data for {stock_name} ({stock_code})")
        self.request_stock_data(stock_code)

    def request_stock_data(self, stock_code):
        """
        일봉 데이터를 요청합니다.
        """
        self.data = []
        end_date = datetime.datetime.now()
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
        """
        일봉 데이터를 MySQL에 저장합니다.
        """
        if not self.current_stock:
            print("[ERROR] No current stock data to save.")
            return

        stock_code, stock_name = self.current_stock

        try:
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()

            # 기존 데이터 삭제
            delete_query = "DELETE FROM stock_datas WHERE stock_idx = %s"
            cursor.execute(delete_query, (stock_code,))
            print(f"[INFO] Existing data for stock code {stock_code} deleted.")

            # 새로운 데이터 삽입
            insert_query = """
            INSERT INTO stock_datas (stock_idx, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            insert_values = [
                (stock_code, record["date"], record["open"], record["high"], record["low"], record["close"], record["volume"])
                for record in self.data
            ]
            cursor.executemany(insert_query, insert_values)
            connection.commit()
            print(f"[INFO] Inserted {len(insert_values)} rows for stock code {stock_code}.")

        except Error as err:
            print(f"[ERROR] Database error while saving data for stock {stock_code}: {err}")

        finally:
            cursor.close()
            connection.close()

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


def periodic_save_real_data(kiwoom, interval=5):
    while True:
        time.sleep(interval)

        # 실시간 데이터가 없거나 장이 닫혀 있으면 저장하지 않음
        if not kiwoom.real_data:
            print("[INFO] No real-time data available. Skipping database save.")
            continue

        # 장 종료 시간 이후 데이터 저장 방지
        now = datetime.datetime.now()
        market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
        if now > market_close_time:
            print("[INFO] Market is closed. Skipping real-time data save.")
            continue

        try:
            connection = kiwoom.db_pool.get_connection()
            cursor = connection.cursor()

            query = """
            INSERT INTO realtime_stocks (stock_idx, current_price, create_at)
            VALUES (%s, %s, NOW())
            """
            values = [(code, info["current_price"]) for code, info in kiwoom.real_data.items()]

            cursor.executemany(query, values)
            connection.commit()

            print(f"[DEBUG] Real-time data saved: {len(values)} records")
        except Error as err:
            print(f"[ERROR] Database error: {err}")
        finally:
            cursor.close()
            connection.close()



def periodic_save_daily_data(kiwoom):
    while True:
        now = datetime.datetime.now()
        if now.hour == 15 and now.minute == 32:  # 일봉 데이터를 저장할 시간 설정
            kiwoom.fetch_stock_list()
            kiwoom.process_next_stock()
        time.sleep(60)


def main():
    # MySQL 연결 풀 생성
    db_pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        host="project-db-cgi.smhrd.com",
        user="mp_24K_DCX13_p3_2",
        password="smhrd2",
        database="mp_24K_DCX13_p3_2",
        port=3307,
        ssl_disabled=True
    )

    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI(db_pool)
    kiwoom.login()

    while not kiwoom.connected:
        app.processEvents()

    kiwoom.fetch_stock_list()
    stock_codes = ";".join(code for code, _ in kiwoom.stock_list)
    kiwoom.request_real_data("1000", stock_codes, "10")

    save_real_thread = threading.Thread(target=periodic_save_real_data, args=(kiwoom,), daemon=True)
    save_real_thread.start()

    save_daily_thread = threading.Thread(target=periodic_save_daily_data, args=(kiwoom,), daemon=True)
    save_daily_thread.start()

    app.exec_()


if __name__ == "__main__":
    main()
