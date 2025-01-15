import sys  # 시스템 관련 기능
import csv  # CSV 파일 저장 기능
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget  # 키움 API 컨트롤
from datetime import datetime
import schedule
import time

class KiwoomAPI:
    def __init__(self):
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.data = []  # 데이터를 저장할 리스트

        # 로그인
        self.kiwoom.dynamicCall("CommConnect()")
        self.kiwoom.OnEventConnect.connect(self.login_event)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata_event)

    def login_event(self, err_code):
        if err_code == 0:
            print("로그인 성공")
            self.request_stock_data("035420", "20241231")  # 삼성전자 데이터 요청
        else:
            print(f"로그인 실패: {err_code}")
            QApplication.instance().exit()

    def request_stock_data(self, stock_code, date):
        print(f"데이터 요청: 종목코드={stock_code}, 기준일자={date}")
        self.data = []
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        result = self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")
        if result != 0:
            print(f"TR 요청 실패: {result}")

    def receive_trdata_event(self, screen_no, rqname, trcode, recordname, prev_next):
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

                self.data.append({
                    "date": date,
                    "open": int(open_price),
                    "high": int(high_price),
                    "low": int(low_price),
                    "close": int(close_price),
                    "volume": int(volume),
                })

                # 디버깅: 현재 데이터 출력
                print(f"수집 중: 일자={date}, 시가={open_price}, 고가={high_price}, 저가={low_price}, 종가={close_price}, 거래량={volume}")

            if prev_next == "2":
                print("다음 데이터 요청 중...")
                self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 2, "0101")
            else:
                self.print_and_save_data()

    def print_and_save_data(self):
        print("수집된 주식 데이터:")
        for idx, row in enumerate(self.data):
            print(f"{idx + 1}: 일자: {row['date']}, 시가: {row['open']}, 고가: {row['high']}, 저가: {row['low']}, 종가: {row['close']}, 거래량: {row['volume']}")

        # 데이터를 CSV로 저장
        self.save_to_csv()

    def save_to_csv(self):
        filename = f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["date", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            writer.writerows(self.data)
        print(f"데이터가 CSV 파일로 저장되었습니다: {filename}")

# 스케줄러 함수
def job():
    print(f"스케줄 실행: {datetime.now()}")
    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI()
    app.exec_()

if __name__ == "__main__":
    schedule.every().day.at("00:00").do(job)  # 매일 자정 실행
    print("스케줄러가 실행 중입니다. 프로그램을 종료하지 마세요.")

    while True:
        schedule.run_pending()
        time.sleep(1)
