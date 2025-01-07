import csv  # CSV 파일 저장을 위한 라이브러리
import sys  # 시스템 관련 기능
import os  # 파일 관련 라이브러리
from PyQt5.QtWidgets import QApplication  # PyQt 애플리케이션 생성
from PyQt5.QAxContainer import QAxWidget  # 키움 API 컨트롤
from pykiwoom.kiwoom import Kiwoom  # PyKiwoom 라이브러리

class KiwoomAPI:
    def __init__(self):
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 로그인 상태를 체크하기 위해 파일 존재 여부 확인
        self.login_file = "kiwoom_login_status.txt"
        if os.path.exists(self.login_file):
            with open(self.login_file, "r") as file:
                login_status = file.read().strip()
            if login_status == "logged_in":
                print("이미 로그인 되어 있습니다.")
                return  # 이미 로그인된 상태에서 처리
            else:
                print("로그인 상태가 아닙니다. 로그인 시도 중...")
        else:
            print("로그인 상태 확인 파일이 없습니다. 로그인 시도 중...")

        # 로그인 호출
        self.kiwoom.dynamicCall("CommConnect()")
        self.kiwoom.OnEventConnect.connect(self.login_event)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata_event)

        self.data = []  # 데이터를 저장할 리스트

    def login_event(self, err_code):
        if err_code == 0:
            print("로그인 성공")
            self.save_login_status()  # 로그인 상태 저장
            self.request_stock_data("035420", "20241231")  # 삼성전자 데이터 요청
        else:
            print(f"로그인 실패: {err_code}")
            QApplication.instance().exit()

    def save_login_status(self):
        with open(self.login_file, "w") as file:
            file.write("logged_in")
        print("로그인 상태 저장 완료")

    def request_stock_data(self, stock_code, date):
        """
        주식 데이터를 요청하는 함수
        """
        connect_state = self.kiwoom.dynamicCall("GetConnectState()")
        print(f"로그인 상태: {connect_state}")
        if connect_state != 1:
            print("로그인이 유효하지 않습니다.")
            return

        print(f"데이터 요청: 종목코드={stock_code}, 기준일자={date}")
        self.data = []
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        result = self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")
        if result != 0:
            print(f"TR 요청 실패: {result}")
            return
        print("TR 요청 성공")

    def receive_trdata_event(self, screen_no, rqname, trcode, recordname, prev_next):
        """
        TR 데이터 수신 이벤트 처리
        """
        print(f"TR 데이터 수신 이벤트 호출: rqname={rqname}, trcode={trcode}, prev_next={prev_next}")
        if rqname == "주식일봉차트조회":
            data_count = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            print(f"수신된 데이터 개수: {data_count}")

            for i in range(data_count):
                date = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()
                open_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()
                high_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()
                low_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()
                close_price = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()
                volume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()

                # 빈 값 처리
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

                # 1년치 데이터만 저장
                if int(date) >= 20230101:
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
                    QApplication.instance().exit()  # 반복 요청 중단
                    return  # 함수 종료

            # 반복 요청 처리
            if prev_next == "2":
                print("다음 데이터 요청...")
                self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 2, "0101")
            else:
                print("모든 데이터 요청 완료")
                print(f"수집된 데이터: {len(self.data)}개")
                QApplication.instance().exit()

    def save_to_csv(self, file_name):
        """
        수집된 데이터를 CSV 파일로 저장하는 함수
        """
        with open(file_name, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["date", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            writer.writerows(self.data)
        print(f"데이터가 {file_name} 파일에 저장되었습니다.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI()
    app.exec_()

    # 수집된 데이터 출력
    print("수집된 데이터 샘플:")
    for row in kiwoom.data[:5]:  # 상위 5개 데이터 출력
        print(row)

    # 데이터를 CSV 파일로 저장
    kiwoom.save_to_csv("../webServer/data/stock_data.csv")
