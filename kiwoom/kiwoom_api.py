import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget


class KiwoomAPI:
    def __init__(self):
        # Kiwoom OpenAPI+ Control 객체 생성
        self.app = QApplication(sys.argv)
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")  # 키움 API COM 객체
        self.connected = False
        self.data_received = False

        # 이벤트 핸들러 연결
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)

        self.data = []

    def _on_event_connect(self, err_code):
        """로그인 이벤트 콜백"""
        if err_code == 0:
            print("로그인 성공")
            self.connected = True
        else:
            print(f"로그인 실패 (Error code: {err_code})")
        self.app.exit()

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        """데이터 수신 이벤트 콜백"""
        if rqname == "OPT10081":
            count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(count):
                date = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자"
                ).strip()
                open_price = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가"
                ).strip()
                high_price = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가"
                ).strip()
                low_price = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가"
                ).strip()
                close_price = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가"
                ).strip()
                volume = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량"
                ).strip()

                self.data.append({
                    "날짜": date,
                    "시가": open_price,
                    "고가": high_price,
                    "저가": low_price,
                    "종가": close_price,
                    "거래량": volume
                })

            self.data_received = True
            self.app.exit()

    def login(self):
        """로그인 실행"""
        self.ocx.dynamicCall("CommConnect()")
        self.app.exec_()
        if not self.connected:
            raise Exception("로그인 실패")

    def get_stock_history(self, stock_code, start_date):
        """과거 주식 데이터 요청"""
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "기준일자", start_date)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "OPT10081", "OPT10081", 0, "0101")
        self.app.exec_()
        if not self.data_received:
            raise Exception("데이터 수신 실패")
        return self.data
