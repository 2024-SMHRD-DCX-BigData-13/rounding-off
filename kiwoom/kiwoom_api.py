from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
import mysql.connector


class KiwoomAPI(QAxWidget):
    def __init__(self, db_connection):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.db_connection = db_connection
        self.account_list = []
        self.real_data = {}
        self.stock_list = []

        # 이벤트 연결
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_trdata)
        self.OnReceiveRealData.connect(self._on_receive_real_data)

    def login(self):
        """Kiwoom API 로그인"""
        print("[INFO] Attempting to log in...")
        self.dynamicCall("CommConnect()")

    def _on_event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            print("[INFO] Login successful!")
            self.connected = True
            account_data = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            self.account_list = account_data.rstrip(";").split(";")
            print(f"[INFO] Account list: {self.account_list}")
        else:
            print(f"[ERROR] Login failed with error code: {err_code}")

    def fetch_stock_list(self):
        """DB에서 주식 목록 가져오기"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT stock_idx, stock_name FROM stocks")
        self.stock_list = cursor.fetchall()

    def request_real_data(self, screen_no, codes, fid_list):
        """실시간 데이터 요청"""
        result = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, codes, fid_list, "0")
        if result == 0:
            print(f"[INFO] Real-time data registration successful for codes: {codes}")
        else:
            print("[ERROR] Real-time data registration failed.")

    def _on_receive_real_data(self, code, real_type, data):
        """실시간 데이터 수신 이벤트"""
        print(f"[DEBUG] OnReceiveRealData called. Code: {code}, Real Type: {real_type}")
        raw_price = self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
        current_price = self._clean_price(raw_price)

        if current_price > 0:
            self.real_data[code] = {"current_price": current_price}
            print(f"[INFO] Real-time Data: {code} - Price: {current_price}")

    @staticmethod
    def _clean_price(raw_price):
        """실시간 데이터에서 가격 파싱"""
        try:
            return abs(int(raw_price))
        except ValueError:
            print(f"[ERROR] Invalid price format: {raw_price}")
            return 0

    def request_historical_data(self, stock_code, start_date, end_date):
        """6개월 간의 과거 데이터 요청"""
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "HistoricalDataRequest", stock_code, 0, "2000")

    def _on_receive_trdata(self, screen_no, rqname, trcode, record_name, prev_next):
        """TR 데이터 수신 이벤트 핸들러"""
        print(f"[DEBUG] OnReceiveTrData called. Screen No: {screen_no}, Request Name: {rqname}")
        if rqname == "historical_data_request":
            total_data_count = int(self.dynamicCall("GetCommDataCount(QString, QString)", trcode, record_name))
            for i in range(total_data_count):
                stock_date = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "일자")
                open_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "시가")
                highest_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "고가")
                lowest_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "저가")
                close_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "종가")
                trade_volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, record_name, i, "거래량")

                self.save_historical_data_to_db(stock_code, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume)

    def save_historical_data_to_db(self, stock_code, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume):
        """과거 데이터를 DB에 저장"""
        try:
            cursor = self.db_connection.cursor()
            query = """
                INSERT INTO stock_datas (stock_idx, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (stock_code, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume))
            self.db_connection.commit()
            print(f"[INFO] Historical data saved: {stock_code} - {stock_date}")
        except mysql.connector.Error as err:
            print(f"[ERROR] Database error: {err}")
