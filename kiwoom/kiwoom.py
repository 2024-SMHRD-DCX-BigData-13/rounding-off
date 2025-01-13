import sys
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from fastapi import FastAPI

app = FastAPI()
stop_event = threading.Event()

class KiwoomAPI:
    def __init__(self):
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.data = []  # 과거 데이터를 저장
        self.real_data = []  # 실시간 데이터를 저장
        self.setup_api()

    def setup_api(self):
        self.kiwoom.dynamicCall("CommConnect()")
        self.kiwoom.OnEventConnect.connect(self.login_event)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata_event)
        self.kiwoom.OnReceiveRealData.connect(self.receive_realdata_event)

    def login_event(self, err_code):
        if err_code == 0:
            print("[KiwoomAPI] 로그인 성공")
        else:
            print(f"[KiwoomAPI] 로그인 실패: {err_code}")

    def request_stock_data(self, stock_code, date):
        """
        과거 데이터를 요청
        """
        self.data = []  # 이전 데이터를 초기화
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")

    def receive_trdata_event(self, screen_no, rqname, trcode, recordname, prev_next):
        if rqname == "주식일봉차트조회":
            data_count = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(data_count):
                date = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()
                open_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()
                high_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()
                low_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()
                close_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()
                volume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()

                self.data.append({
                    "date": date,
                    "open": int(open_price) if open_price else 0,
                    "high": int(high_price) if high_price else 0,
                    "low": int(low_price) if low_price else 0,
                    "close": int(close_price) if close_price else 0,
                    "volume": int(volume) if volume else 0,
                })

            if prev_next == "2":
                self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 2, "0101")

    def receive_realdata_event(self, stock_code, real_type, real_data):
        """
        실시간 데이터 수신 이벤트
        """
        self.real_data.append({"stock_code": stock_code, "real_type": real_type, "real_data": real_data})

    def get_data(self):
        return self.data

    def get_real_time_data(self):
        return self.real_data


kiwoom = None

def run_kiwoom():
    global kiwoom
    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI()
    while not stop_event.is_set():
        app.processEvents()

threading.Thread(target=run_kiwoom, daemon=True).start()

@app.get("/get-data")
def get_stock_data():
    if kiwoom:
        return {"data": kiwoom.get_data()}
    return {"error": "Kiwoom API is not initialized."}

@app.get("/get-real-time-data")
def get_real_time_data():
    if kiwoom:
        return {"data": kiwoom.get_real_time_data()}
    return {"error": "Kiwoom API is not initialized."}

@app.post("/request-past-data/{stock_code}/{date}")
def request_past_data(stock_code: str, date: str):
    if kiwoom:
        kiwoom.request_stock_data(stock_code, date)
        return {"message": f"Past data requested for stock_code={stock_code}, date={date}"}
    return {"error": "Kiwoom API is not initialized."}
