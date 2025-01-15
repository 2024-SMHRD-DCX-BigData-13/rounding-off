from fastapi import FastAPI  # FastAPI 라이브러리를 임포트하여 웹 서버 애플리케이션을 작성합니다.
from pydantic import BaseModel  # 데이터 유효성 검사를 위한 Pydantic 모델을 정의합니다.
from PyQt5.QAxContainer import QAxWidget  # PyQt5의 QAxWidget 클래스를 임포트하여 Kiwoom OpenAPI와의 연동을 처리합니다.
from PyQt5.QtWidgets import QApplication  # PyQt5의 QApplication 클래스를 임포트하여 GUI 애플리케이션을 실행합니다.
import sys  # 시스템 관련 모듈을 임포트하여 명령줄 인수 등을 처리합니다.
import threading  # threading 모듈을 임포트하여 멀티스레딩 작업을 지원합니다.

app = FastAPI()  # FastAPI 애플리케이션 인스턴스를 생성합니다.

data_store = []  # 데이터를 저장할 전역 리스트

class KiwoomAPI:
    def __init__(self):
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")  # Kiwoom OpenAPI 컨트롤러 객체를 생성합니다.
        self.kiwoom.dynamicCall("CommConnect()")  # Kiwoom OpenAPI에 로그인 요청을 보냅니다.
        self.kiwoom.OnEventConnect.connect(self.login_event)  # 로그인 이벤트와 login_event 메서드를 연결합니다.
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata_event)  # TR 데이터 수신 이벤트와 receive_trdata_event 메서드를 연결합니다.

        self.data = []  # 데이터를 저장할 리스트

    def login_event(self, err_code):
        if err_code == 0:  # 로그인 성공 여부를 확인합니다.
            print("로그인 성공")
            self.request_stock_data("035420", "20241231")  # 삼성전자 주식 데이터를 요청합니다.
        else:
            print(f"로그인 실패: {err_code}")  # 로그인 실패 시 에러 코드를 출력합니다.

    def request_stock_data(self, stock_code, date):
        connect_state = self.kiwoom.dynamicCall("GetConnectState()")  # 로그인 상태를 확인합니다.
        print(f"로그인 상태: {connect_state}")
        if connect_state != 1:  # 로그인이 유효하지 않은 경우 처리합니다.
            print("로그인이 유효하지 않습니다.")
            return

        print(f"데이터 요청: 종목코드={stock_code}, 기준일자={date}")
        self.data = []  # 기존 데이터를 초기화합니다.
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)  # 요청할 종목 코드를 설정합니다.
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)  # 요청할 기준일자를 설정합니다.
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")  # 수정 주가 구분을 설정합니다.

        result = self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")  # 주식 데이터를 요청합니다.
        if result != 0:  # 요청 실패 시 에러를 출력합니다.
            print(f"TR 요청 실패: {result}")
            return
        print("TR 요청 성공")

    def receive_trdata_event(self, screen_no, rqname, trcode, recordname, prev_next):
        print(f"TR 데이터 수신 이벤트 호출: rqname={rqname}, trcode={trcode}, prev_next={prev_next}")  # 이벤트 호출 로그를 출력합니다.
        if rqname == "주식일봉차트조회":
            data_count = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)  # 수신된 데이터의 개수를 가져옵니다.
            print(f"수신된 데이터 개수: {data_count}")

            for i in range(data_count):
                date = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()  # 일자를 가져옵니다.
                open_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()  # 시가를 가져옵니다.
                high_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()  # 고가를 가져옵니다.
                low_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()  # 저가를 가져옵니다.
                close_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()  # 종가를 가져옵니다.
                volume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()  # 거래량을 가져옵니다.

                if close_price == "":
                    close_price = 0
                if open_price == "":
                    open_price = 0
                if high_price == "":
                    high_price = 0
                if low_price == "":
                    low_price = 0
                if volume == "":
                    volume = 0

                if int(date) >= 20230101:  # 2023년 이후의 데이터만 저장합니다.
                    self.data.append({
                        "date": date,
                        "open": int(open_price),
                        "high": int(high_price),
                        "low": int(low_price),
                        "close": int(close_price),
                        "volume": int(volume),
                    })
                    print(f"일자: {date}, 시가: {open_price}, 고가: {high_price}, 저가: {low_price}, 종가: {close_price}, 거래량: {volume}")
                else:
                    print("요청 범위를 벗어나는 데이터입니다. 반복 요청 중단.")
                    return

            global data_store
            data_store.extend(self.data)  # 수집된 데이터를 전역 리스트에 저장합니다.

            if prev_next == "2":  # 추가 데이터가 있을 경우 반복 요청합니다.
                print("다음 데이터 요청...")
                self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 2, "0101")
            else:
                print("모든 데이터 요청 완료")

@app.on_event("startup")
def startup_event():
    def run_qt_app():
        app = QApplication(sys.argv)  # PyQt 애플리케이션을 실행합니다.
        kiwoom = KiwoomAPI()  # KiwoomAPI 객체를 생성합니다.
        app.exec_()  # 이벤트 루프를 실행합니다.

    qt_thread = threading.Thread(target=run_qt_app)  # PyQt 애플리케이션을 별도의 스레드에서 실행합니다.
    qt_thread.start()

@app.get("/data")
def get_data():
    return {"data": data_store}  # 전역 변수에 저장된 데이터를 JSON 형식으로 반환합니다.
