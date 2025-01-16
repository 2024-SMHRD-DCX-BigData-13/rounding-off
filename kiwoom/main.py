# import sys  # 시스템 관련 기능
# import csv  # CSV 파일 저장 기능
# import os  # 파일 및 디렉토리 관리 기능
# from PyQt5.QtWidgets import QApplication
# from PyQt5.QAxContainer import QAxWidget  # 키움 API 컨트롤
# from datetime import datetime, timedelta
# import schedule
# import time

# class KiwoomAPI:
#     def __init__(self, app):
#         self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
#         self.app = app  # QApplication 인스턴스
#         self.data = []
#         self.current_stock = None
#         self.stock_list = []

#     def login(self, stock_list):
#         self.stock_list = stock_list
#         self.kiwoom.dynamicCall("CommConnect()")
#         self.kiwoom.OnEventConnect.connect(self.login_event)
#         self.kiwoom.OnReceiveTrData.connect(self.receive_trdata_event)

#     def login_event(self, err_code):
#         if err_code == 0:
#             print("로그인 성공")
#             self.process_next_stock()
#         else:
#             print(f"로그인 실패: {err_code}")
#             self.app.quit()

#     def process_next_stock(self):
#         if not self.stock_list:
#             print("모든 종목 데이터 처리가 완료되었습니다.")
#             self.app.quit()
#             return

#         self.current_stock = self.stock_list.pop(0)
#         stock_code, stock_name = self.current_stock
#         print(f"데이터 요청 시작: {stock_name} ({stock_code})")
#         self.request_stock_data(stock_code)

#     def request_stock_data(self, stock_code):
#         self.data = []
#         end_date = datetime.now()
#         start_date = end_date - timedelta(days=2 * 365)
#         formatted_date = end_date.strftime("%Y%m%d")

#         self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
#         self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", formatted_date)
#         self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
#         self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")

#     def receive_trdata_event(self, screen_no, rqname, trcode, recordname, prev_next):
#         if rqname == "주식일봉차트조회":
#             data_count = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
#             print(f"수신된 데이터 개수: {data_count}")

#             for i in range(data_count):
#                 date = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()
#                 open_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()
#                 high_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()
#                 low_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()
#                 close_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()
#                 volume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()

#                 self.data.append({
#                     "date": date,
#                     "open": int(open_price),
#                     "high": int(high_price),
#                     "low": int(low_price),
#                     "close": int(close_price),
#                     "volume": int(volume)
#                 })

#             self.save_to_csv()

#             # 1초 간격 추가
#             time.sleep(1)
#             self.process_next_stock()

#     def save_to_csv(self):
#         if not self.current_stock:
#             return

#         stock_code, stock_name = self.current_stock
#         directory = "../webServer/kiwoomData"
#         filename = f"{directory}/{stock_name}.csv"
#         os.makedirs(directory, exist_ok=True)

#         with open(filename, mode="w", newline="", encoding="utf-8") as file:
#             writer = csv.DictWriter(file, fieldnames=["date", "open", "high", "low", "close", "volume"])
#             writer.writeheader()
#             writer.writerows(self.data)
#         print(f"{stock_name} 데이터가 CSV 파일로 저장되었습니다: {filename}")

# # 스케줄러 함수
# def job():
#     stock_list = [
#         ("005930", "삼성전자"),
#         ("000660", "SK하이닉스"),
#         ("035420", "NAVER"),
#         ("005380", "현대자동차"),
#         ("035720", "카카오"),
#         ("051910", "LG화학"),
#         ("005490", "POSCO홀딩스"),
#         ("207940", "삼성바이오로직스"),
#         ("096770", "SK이노베이션"),
#         ("068270", "셀트리온"),
#         ("006400", "삼성SDI"),
#         ("012330", "현대모비스"),
#         ("000270", "기아"),
#         ("066570", "LG전자"),
#         ("323410", "카카오뱅크"),
#         ("034020", "두산에너빌리티"),
#         ("009830", "한화솔루션"),
#         ("015760", "한국전력"),
#         ("011200", "HMM"),
#         ("000120", "CJ대한통운")
#     ]

#     app = QApplication(sys.argv)
#     kiwoom = KiwoomAPI(app)
#     kiwoom.login(stock_list)
#     app.exec_()

# if __name__ == "__main__":
#     schedule.every().day.at("09:34").do(job)  # 매일 자정 실행
#     print("스케줄러가 실행 중입니다. 프로그램을 종료하지 마세요.")

#     while True:
#         schedule.run_pending()
#         time.sleep(1)
# kiwoom_api_server.py
# kiwoom_api_server.py




# from fastapi import FastAPI
# from datetime import datetime

# app = FastAPI()

# # 최신 데이터 저장 (예시 데이터)
# latest_data = {
#     "stock_code": "005930",
#     "price": 64000,
#     "volume": 1200,
#     "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# }

# # 최신 데이터 업데이트 함수 (실제 키움 API 데이터를 갱신해야 함)
# @app.get("/update-data")
# def update_data():
#     global latest_data
#     # 데이터를 키움 API에서 받아오는 로직 추가 필요
#     latest_data["price"] += 10  # 예시: 가격 증가
#     latest_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     return {"message": "Data updated", "latest_data": latest_data}

# # 실시간 데이터 제공 엔드포인트
# @app.get("/latest-data")
# def get_latest_data():
#     return latest_data

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from fastapi import FastAPI, WebSocket, HTTPException
import threading
import asyncio
import time

app = FastAPI()

class KiwoomAPI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.real_data = {}  # 실시간 데이터를 저장할 딕셔너리
        self.current_stock_code = None  # 현재 요청된 종목 코드

        # 로그인 호출
        self.kiwoom.dynamicCall("CommConnect()")
        self.kiwoom.OnEventConnect.connect(self.on_event_connect)
        self.kiwoom.OnReceiveRealData.connect(self.on_receive_real_data)

    def on_event_connect(self, err_code):
        """
        로그인 이벤트 핸들러
        """
        if err_code == 0:
            print("키움 API 로그인 성공")
        else:
            print(f"키움 API 로그인 실패: {err_code}")
            self.app.quit()

    def set_real_reg(self, code):
        """
        실시간 데이터 요청 등록.
        """
        screen_no = "1000"  # 고유한 화면 번호 설정
        fid_list = "10;15"  # 현재가(10), 거래량(15)
        real_type = "0"  # 마지막 등록 실시간 해제 후 등록
        self.kiwoom.dynamicCall(
            "SetRealReg(QString, QString, QString, QString)",
            screen_no, code, fid_list, real_type
        )
        self.current_stock_code = code
        print(f"실시간 데이터 요청 등록: {code}")

    def on_receive_real_data(self, code, real_type, real_data):
        """
        실시간 데이터 수신 이벤트 핸들러
        """
        if real_type == "주식체결" and code == self.current_stock_code:
            price = self.kiwoom.dynamicCall(
                "GetCommRealData(QString, int)", code, 10
            ).strip()  # 현재가
            volume = self.kiwoom.dynamicCall(
                "GetCommRealData(QString, int)", code, 15
            ).strip()  # 거래량
            self.real_data[code] = {
                "price": int(price) if price else 0,
                "volume": int(volume) if volume else 0,
            }
            print(f"실시간 데이터 수신: {code} - 가격: {price}, 거래량: {volume}")

    async def push_real_data(self, websocket: WebSocket):
        """
        WebSocket을 통해 실시간 데이터를 메인 서버로 전송
        """
        while True:
            if self.current_stock_code in self.real_data:
                data = self.real_data[self.current_stock_code]
                await websocket.send_json(data)
            else:
                print("실시간 데이터 없음")
            await asyncio.sleep(1)

    def run(self):
        self.app.exec_()

kiwoom_instance = None

@app.on_event("startup")
def startup_event():
    """
    키움 API 초기화 및 실시간 데이터 요청 시작
    """
    global kiwoom_instance

    def start_kiwoom_api():
        global kiwoom_instance
        kiwoom_instance = KiwoomAPI()
        time.sleep(5)
        # 실시간 데이터 요청 등록
        stock_code = "005930"  # 예: 삼성전자
        kiwoom_instance.set_real_reg(stock_code)

        kiwoom_instance.run()

    threading.Thread(target=start_kiwoom_api, daemon=True).start()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 클라이언트로 실시간 데이터 전송
    """
    await websocket.accept()
    try:
        if kiwoom_instance:
            await kiwoom_instance.push_real_data(websocket)
    except Exception as e:
        print(f"WebSocket 연결 종료: {e}")
