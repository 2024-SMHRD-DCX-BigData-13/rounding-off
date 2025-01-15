import sys
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
import threading

app = FastAPI()

class KiwoomAPI:
    def __init__(self):
        self.app = QApplication(sys.argv)  # PyQt5 애플리케이션 생성
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.dynamicCall("CommConnect()")
        self.kiwoom.OnEventConnect.connect(self.login_event)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata_event)
        self.data = []
        self.request_completed = False

    def login_event(self, err_code):
        if err_code == 0:
            print("로그인 성공")
        else:
            print(f"로그인 실패: {err_code}")
            self.app.exit()

    def request_stock_data(self, stock_code, start_date, end_date):
        """
        주식 데이터를 요청합니다.
        """
        print(f"데이터 요청: 종목코드={stock_code}, 시작일자={start_date}, 종료일자={end_date}")
        self.data = []
        self.request_completed = False
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", end_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        result = self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")
        if result != 0:
            print(f"TR 요청 실패: {result}")
            self.request_completed = True

    def receive_trdata_event(self, screen_no, rqname, trcode, recordname, prev_next):
        """
        TR 데이터 수신 이벤트 핸들러
        """
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
                    "open": int(open_price),
                    "high": int(high_price),
                    "low": int(low_price),
                    "close": int(close_price),
                    "volume": int(volume),
                })

            if prev_next == "2":
                self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 2, "0101")
            else:
                self.request_completed = True

kiwoom_api = None

@app.on_event("startup")
def startup_event():
    """
    PyQt5와 Kiwoom API 초기화
    """
    global kiwoom_api

    def run_qt_loop():
        global kiwoom_api
        kiwoom_api = KiwoomAPI()
        kiwoom_api.app.exec_()

    threading.Thread(target=run_qt_loop, daemon=True).start()

@app.get("/send-data")
async def send_data():
    """
    키움 API 데이터를 수집하고 반환하는 엔드포인트
    """
    if not kiwoom_api:
        raise HTTPException(status_code=500, detail="Kiwoom API not initialized")
    try:
        start_date = (datetime.today() - timedelta(days=365 * 2)).strftime("%Y%m%d")
        end_date = datetime.today().strftime("%Y%m%d")
        kiwoom_api.request_stock_data("035420", start_date, end_date)

        while not kiwoom_api.request_completed:
            await asyncio.sleep(0.1)

        if not kiwoom_api.data:
            raise HTTPException(status_code=500, detail="No data received from Kiwoom API")
        
        return {"data": kiwoom_api.data}

    except Exception as e:
        print(f"키움 API 서버 에러: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")
