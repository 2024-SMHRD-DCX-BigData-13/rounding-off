import sys  # 시스템 관련 기능
import os  # 파일 및 디렉토리 관리 기능
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget  # 키움 API 컨트롤
from datetime import datetime, timedelta
import pymysql
import schedule
import time

class KiwoomAPI:
    def __init__(self, app, db_connection):
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.app = app  # QApplication 인스턴스
        self.db_connection = db_connection  # MySQL 연결 객체
        self.data = []
        self.current_stock = None
        self.stock_list = []

    def login(self):
        self.stock_list = self.fetch_stock_list_from_db()
        if not self.stock_list:
            print("DB에서 가져온 종목 코드가 없습니다.")
            self.app.quit()
            return

        self.kiwoom.dynamicCall("CommConnect()")
        self.kiwoom.OnEventConnect.connect(self.login_event)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata_event)

    def login_event(self, err_code):
        if err_code == 0:
            print("로그인 성공")
            self.process_next_stock()
        else:
            print(f"로그인 실패: {err_code}")
            self.app.quit()

    def fetch_stock_list_from_db(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT stock_idx, stock_name FROM stocks")
        stock_list = cursor.fetchall()
        # 튜플 형태를 리스트로 변환
        return list(stock_list)

    def process_next_stock(self):
        if not self.stock_list:
            print("모든 종목 데이터 처리가 완료되었습니다.")
            self.app.quit()
            return

        # 리스트에서 pop을 사용해 종목 제거
        self.current_stock = self.stock_list.pop(0)
        stock_code, stock_name = self.current_stock
        print(f"데이터 요청 시작: {stock_name} ({stock_code})")
        self.request_stock_data(stock_code)

    def request_stock_data(self, stock_code):
        self.data = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2 * 365)
        formatted_date = end_date.strftime("%Y%m%d")

        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", formatted_date)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")

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
                    "volume": int(volume)
                })

            self.save_to_db()

            # 1초 간격 추가
            time.sleep(1)
            self.process_next_stock()

    def save_to_db(self):
        if not self.current_stock:
            return

        stock_code, stock_name = self.current_stock
        cursor = self.db_connection.cursor()

        for record in self.data:
            cursor.execute(
                """
                INSERT INTO stock_datas (stock_idx, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (stock_code, record["date"], record["open"], record["high"], record["low"], record["close"], record["volume"])
            )

        self.db_connection.commit()
        print(f"{stock_name} 데이터가 DB에 저장되었습니다.")

# 스케줄러 함수
def job():
    db_connection = pymysql.connect(
        host="localhost",
        user="com",
        password="com01",
        database="books",
        charset="utf8mb4"
    )

    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI(app, db_connection)
    kiwoom.login()
    app.exec_()
    db_connection.close()

if __name__ == "__main__":
    schedule.every().day.at("12:07").do(job)  # 매일 자정 실행
    print("스케줄러가 실행 중입니다. 프로그램을 종료하지 마세요.")

    while True:
        schedule.run_pending()
        time.sleep(1)
