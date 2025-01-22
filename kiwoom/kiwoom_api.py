import pythoncom
import win32com.client
import time


class KiwoomAPI:
    def __init__(self):
        self.ocx = win32com.client.Dispatch("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.account_list = []
        self.real_data = {}
        self.stock_list = []

        # 이벤트 핸들러 연결
        self.ocx.OnEventConnect = self._on_event_connect
        self.ocx.OnReceiveTrData = self._on_receive_trdata
        self.ocx.OnReceiveRealData = self._on_receive_real_data

    def login(self):
        """로그인 요청"""
        print("[INFO] Attempting to log in...")
        self.ocx.CommConnect()
        while not self.connected:
            pythoncom.PumpWaitingMessages()

    def _on_event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            print("[INFO] Login successful!")
            self.connected = True
            account_data = self.ocx.GetLoginInfo("ACCNO")
            self.account_list = account_data.rstrip(";").split(";")
            print(f"[INFO] Account list: {self.account_list}")
        else:
            print(f"[ERROR] Login failed with error code: {err_code}")

    def fetch_stock_list(self):
        """DB에서 주식 목록 가져오기"""
        self.stock_list = [
            # 샘플 데이터. 실제 데이터는 DB에서 가져오도록 수정 필요.
            ("000660", "SK하이닉스"),
            ("005930", "삼성전자"),
            ("035420", "NAVER")
        ]

    def request_real_data(self, screen_no, codes, fid_list):
        """실시간 데이터 요청"""
        self.ocx.SetRealReg(screen_no, codes, fid_list, "0")
        print(f"[INFO] Real-time data registration successful for codes: {codes}")

    def _on_receive_real_data(self, code, real_type, data):
        """실시간 데이터 수신 이벤트"""
        print(f"[DEBUG] Real-time Data Received - Code: {code}, Type: {real_type}")
        raw_price = self.ocx.GetCommRealData(code, 10).strip()
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
        self.ocx.SetInputValue("종목코드", stock_code)
        self.ocx.SetInputValue("기준일자", end_date)
        self.ocx.SetInputValue("수정주가구분", "1")
        self.ocx.CommRqData("HistoricalDataRequest", "OPT10081", 0, "2000")

    def _on_receive_trdata(self, screen_no, rqname, trcode, record_name, prev_next):
        """TR 데이터 수신 이벤트 핸들러"""
        print(f"[DEBUG] TR Data Received - Screen No: {screen_no}, Request Name: {rqname}")
        if rqname == "HistoricalDataRequest":
            total_data_count = self.ocx.GetRepeatCnt(trcode, record_name)
            for i in range(total_data_count):
                stock_date = self.ocx.GetCommData(trcode, record_name, i, "일자").strip()
                open_price = self.ocx.GetCommData(trcode, record_name, i, "시가").strip()
                highest_price = self.ocx.GetCommData(trcode, record_name, i, "고가").strip()
                lowest_price = self.ocx.GetCommData(trcode, record_name, i, "저가").strip()
                close_price = self.ocx.GetCommData(trcode, record_name, i, "종가").strip()
                trade_volume = self.ocx.GetCommData(trcode, record_name, i, "거래량").strip()

                print(f"[INFO] Historical Data: {stock_date}, Open: {open_price}, High: {highest_price}, "
                      f"Low: {lowest_price}, Close: {close_price}, Volume: {trade_volume}")
