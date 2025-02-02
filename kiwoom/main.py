from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer
from pydantic import BaseModel
from threading import Event
import asyncio
import threading
import datetime
import time
from mysql.connector import pooling, Error

app = FastAPI()
stop_event = Event()
holdings_response_event = asyncio.Event() # 보유 종목 이벤트
trade_history_response_event = asyncio.Event() # 거래 내역 이벤트
account_response_event = asyncio.Event() # 계좌 정보 이벤트
pending_orders_response_event = asyncio.Event() # 미체결 내역 이벤트


# 데이터 정리 함수
def clean_price(raw_price):
    try:
        return abs(int(raw_price))
    except ValueError:
        print(f"[ERROR] Invalid price format: {raw_price}")
        return 0

# 키움 API 클래스 정의
class KiwoomAPI(QAxWidget):
    def __init__(self, db_pool):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        self.login_event_loop = QEventLoop()
        self.data_event_loop = QEventLoop()
        self.connected = False

        self.real_data = {}  # 실시간 데이터 저장
        self.data = []  # 과거 데이터 저장
        self.holdings_data = []  # 보유 종목 저장 리스트
        self.trade_history_data = []  # 거래 내역 저장 리스트
        self.stock_list = []  # 종목 리스트 저장
        self.account_info = {}  # 계좌 정보 저장
        self.pending_orders_data = []  # 미체결 내역 저장

        self.current_stock = None
        self.account_no = None  # 계좌번호 저장

        self.db_pool = db_pool

        # 이벤트 연결
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_trdata)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveMsg.connect(self._on_receive_msg)

    def login(self):
        # 로그인 함수
        print("[DEBUG] Attempting to log in...")
        self.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def _on_event_connect(self, err_code):
        # 로그인 체크 함수
        if err_code == 0:
            print("[DEBUG] Login successful!")
            self.connected = True
            self.account_no = self.dynamicCall("GetLoginInfo(QString)", "ACCNO").strip().split(';')[0]
        else:
            print(f"[ERROR] Login failed with error code: {err_code}")
        self.login_event_loop.exit()

    def request_holdings(self):
        # 보유 종목 조회 요청
        if not self.account_no:
            print("[ERROR] Account number is not available.")
            return

        print("[DEBUG] Requesting holdings data...")

        self.holdings_data = []  # 기존 데이터 초기화

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역조회", "opw00018", 0, "9001")

        # 🔹 QEventLoop 사용 제거 & 비동기 처리
        QTimer.singleShot(5000, lambda: print("[DEBUG] Holdings request completed."))  # 5초 후 로그 확인용

    def request_trade_history(self):
        # 거래 내역 조회 요청
        if not self.account_no:
            print("계좌 번호가 없음")
            return

        print("계좌번호 : ", self.account_no , "거래 내역 조회 요청 중")

        self.trade_history_data = []  # 기존 데이터 초기화
        print("기존 데이터 초기화 완료 : ", self.trade_history_data)

        last_90_days = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y%m%d")  # 🔹 최근 90일 조회

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.dynamicCall("SetInputValue(QString, QString)", "조회기간", last_90_days)  # 🔹 조회 기간 30일로 변경
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")  # 🔹 전체 체결 내역 조회

        result = self.dynamicCall("CommRqData(QString, QString, int, QString)", "체결내역조회", "opw00007", 0, "9002")
        print(f"0이면 요청 성공: {result}")  # 🔹 요청이 정상적으로 들어갔는지 확인

        if result != 0:
            print(f"[ERROR] 거래 내역 요청 실패 (Error Code: {result})")
            return

        print("[INFO] 거래 내역 요청 성공")
    
    def request_account_info(self):
        # 계좌 정보 요청 (예수금, 출금 가능 금액, 주문 가능 금액, 계좌번호)
        if not self.account_no:
            print("[ERROR] Account number is not available.")
            return

        print("계좌 정보 요청!")
        self.account_info = {}  # 기존 데이터 초기화

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황", "opw00001", 0, "9003")

    def request_pending_orders(self):
        # 미체결 내역 요청
        if not self.account_no:
            print("계좌 정보 없음!")
            return

        print("[DEBUG] Requesting pending orders...")
        self.pending_orders_data = []  # 기존 데이터 초기화

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "미체결내역조회", "opt10075", 0, "9004")


    def fetch_stock_list(self):
        print("DB에서 데이터 종목 코드,이름 요청 중")
        try:
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT stock_idx, stock_name FROM stocks")
            self.stock_list = cursor.fetchall()
            print(f"DB에서 받은 데이터 : {self.stock_list}")
        except Error as err:
            print(f"데이터 베이스 에러러: {err}")
        finally:
            cursor.close()
            connection.close()

    def start_stock_requests(self, stock_list):
        """
        주식 리스트를 받아서 순차적으로 조회 요청 시작
        """
        self.stock_list = stock_list
        self.process_next_stock()

    def process_next_stock(self):
        """
        다음 종목 데이터를 요청합니다. 모든 종목이 처리되면 종료.
        """
        if not self.stock_list:
            print("[INFO] 모든 종목 처리 완료.")
            return

        self.current_stock = self.stock_list.pop(0)
        stock_code, stock_name = self.current_stock
        print(f"[INFO] {stock_name} ({stock_code}) 데이터 요청 중...")
        self.request_stock_data(stock_code, stock_name)
    
    def request_stock_data(self, stock_code, stock_name):
        """
        prev_next 없이 한 번의 요청만 사용하여 데이터 가져오기
        """
        print(f"[INFO] {stock_code} 과거 데이터 요청 중...")

        self.data = []
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y%m%d")  # 🔹 2년치 조회

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
        self.dynamicCall("SetInputValue(QString, QString)", "기준일자", end_date)  # 🔹 기준일을 넓게 설정하여 한번에 가져오기
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        result = self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", 0, "0101")

        if result != 0:
            print(f"[ERROR] 요청 실패 - 오류 코드: {result}")
            print("[WARNING] 60초 대기 후 재시도")
            time.sleep(60)  # 🔹 `-300` 발생 시 60초 대기 후 재시도
            return

    def cancel_order(self, order_number):
        """
        키움 API 미체결 주문 취소 요청
        """
        if not self.account_no:
            print("계좌 번호가 없음음")
            return

        print(f"취소할 주문번호: {order_number}")

        result = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                "주문취소",
                "9006",  # 화면번호 (중복 방지)
                self.account_no,  # 계좌번호
                3,  # 주문유형: 3 (취소 주문)
                "",  # 종목코드 (미체결 취소는 종목코드 필요 없음)
                0,  # 수량 (미체결 취소는 수량 필요 없음)
                0,  # 가격 (미체결 취소는 가격 필요 없음)
                "00",  # 호가구분: 지정가
                order_number,  # 원주문번호
            ]
        )
        print(f"취소 요청한 주문번호: {order_number}, 결과: {result}")
        return result

    def _on_receive_trdata(self, screen_no, rqname, trcode, record_name, prev_next, data_len, err_code, msg, sRQName):
        stock_data_cnt = 0
        holding_cnt = 0
        trading_lst_cnt = 0
        pending_cnt = 0
        hold_next = 0
        stock_data_next = 0

        if rqname == "주식일봉차트조회":
            data_count = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

            for i in range(data_count):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip()
                open_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()
                close_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()

                self.data.append({
                    "date": date,
                    "open": int(open_price),
                    "high": int(high_price),
                    "low": int(low_price),
                    "close": int(close_price),
                    "volume": int(volume)
                })

            self.save_to_db()
            time.sleep(3)  # 🔹 요청 간격 조정
            self.process_next_stock()  # 🔹 다음 종목 요청

        elif rqname == "계좌평가잔고내역조회":
            hold_next = prev_next
            print(f"[DEBUG] 받은 TR 데이터: {rqname}, 화면넘버: {screen_no}, 다음요청 여부: {hold_next}")
            holding_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            print(f"[DEBUG] 보유 종목 확인: {holding_cnt}")  # 🔹 데이터 개수 확인 로그 추가

            for i in range(holding_cnt):
                stock_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip()
                current_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip())
                buy_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입가").strip())
                quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량").strip())
                eval_profit = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "평가손익").strip())

                self.holdings_data.append({
                    "stock_name": stock_name,
                    "current_price": current_price,
                    "evaluation_profit": eval_profit,
                    "buy_price": buy_price,
                    "quantity": quantity
                })

            print("저장된 데이터:", self.holdings_data)  # 🔹 데이터가 저장되었는지 확인 로그 추가
            holdings_response_event.set()

        elif rqname == "체결내역조회":
            trading_lst_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            print(f"[DEBUG] TR 응답 받음: {rqname}, count={trading_lst_cnt}, msg={msg}")

            if trading_lst_cnt == 0:
                print("받은 거래내역 데이터 없음!")  # 🔹 데이터가 없는 경우 로그 추가
                return  # 🔹 데이터가 없으면 추가 진행 안 함

            self.trade_history_data.clear()  # 🔹 새로운 요청마다 초기화

            for i in range(trading_lst_cnt):
                date_raw = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결시간").strip()
                stock_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip()
                price_raw = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결가").strip()
                quantity_raw = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결량").strip()
                trade_type = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문구분").strip()

                # 🔹 원본 데이터 로그 추가
                print(f"받은 데이터 - 날짜: {date_raw}, 종목: {stock_name}, 가격: {price_raw}, 수량: {quantity_raw}, 거래타입: {trade_type}")

                # 🔹 데이터가 비어 있으면 "N/A" 처리 (빈 문자열 방지)
                date = date_raw if date_raw else "N/A"
                price = int(price_raw) if price_raw.replace("-", "").isdigit() else "N/A"
                quantity = int(quantity_raw) if quantity_raw.replace("-", "").isdigit() else "N/A"

                self.trade_history_data.append({
                    "date": date,
                    "stock_name": stock_name if stock_name else "N/A",
                    "price": price,
                    "quantity": quantity,
                    "type": trade_type if trade_type else "N/A"
                })

            if self.trade_history_data:
                print("저장된 거래 내역 데이터:", self.trade_history_data)
            else:
                print("아직 거래내역 데이터가 비어있음")

            # 🔹 FastAPI에 데이터 수신 완료 신호 보내기
            trade_history_response_event.set()

        elif rqname == "예수금상세현황":
            print("[DEBUG] Received Account Info Data")
            예수금 = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "예수금").strip())
            출금가능금액 = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "출금가능금액").strip())
            주문가능금액 = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "주문가능금액").strip())

            self.account_info = {
                "account_number": self.account_no,
                "balance": 예수금,
                "available_withdraw": 출금가능금액,
                "order_available": 주문가능금액
            }

            print("받은 계좌 정보 :", self.account_info)
            account_response_event.set()
        
        elif rqname == "미체결내역조회":
            print("[DEBUG] Received Pending Orders Data")
            count = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            print(f"[DEBUG] Pending Orders Count: {count}")

            for i in range(count):
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문번호").strip()
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문시간").strip()
                stock_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip()
                price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문가격").strip())
                quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문수량").strip())
                status = self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문상태").strip()

                self.pending_orders_data.append({
                    "date": date,
                    "stock_name": stock_name,
                    "price": price,
                    "quantity": quantity,
                    "status": status
                })

            print("[INFO] Pending Orders Updated:", self.pending_orders_data)
            pending_orders_response_event.set()


    def save_to_db(self):
        if not self.current_stock:
            print("저장할 주식 데이터가 없음.")
            return

        stock_code, stock_name = self.current_stock
        try:
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()

            delete_query = "DELETE FROM stock_datas WHERE stock_idx = %s"
            cursor.execute(delete_query, (stock_code,))

            insert_query = """
            INSERT INTO stock_datas (stock_idx, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            insert_values = [
                (stock_code, record["date"], record["open"], record["high"], record["low"], record["close"], record["volume"])
                for record in self.data
            ]
            cursor.executemany(insert_query, insert_values)
            connection.commit()
            
            print(f"저장중: {len(insert_values)} 해당종목에 대한 데이터 저장: {stock_code}.")
        except Error as err:
            print(f"[ERROR] Database error: {err}")
        finally:
            cursor.close()
            connection.close()

    def request_real_data(self, screen_no, codes, fid_list):
        try:
            print(f"해당 종목에 대한 실시간 데이터 요청 : {codes}")
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, codes, fid_list, "0")
            print(f"실시간 데이터 요청 성공: {codes}")
        except Exception as e:
            print(f"실시간 데이터 요청 실패: {str(e)}")

    def _on_receive_real_data(self, code, real_type, data):
        if real_type == "주식체결":
            raw_price = self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            current_price = clean_price(raw_price)
            if current_price > 0:
                self.real_data[code] = {"current_price": current_price}
                # print(f"[DEBUG] Real-time data updated for {code}: {current_price}")

    def send_order(self, trade_type, stock_code, quantity, price):
        # 키움 API 매수/매도 요청
        order_type = 1 if trade_type == "BUY" else 2  # 1: 매수, 2: 매도
        result = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                f"{trade_type}주문",  # 요청명
                "1001",  # 화면번호
                self.account_no,  # 계좌번호
                order_type,  # 주문유형
                stock_code,  # 종목코드
                quantity,  # 주문 수량
                price,  # 주문 가격
                "00",  # 호가구분: 지정가
                ""  # 원주문번호: 신규주문일 때 빈 문자열
            ]
        )
        print(f"[INFO] {trade_type} 요청 완료: 종목코드 {stock_code}, 수량 {quantity}, 가격 {price}")
        return result
    
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """
        키움 API 주문 결과 처리
        """
        print(f"[INFO] Received message from Kiwoom API: {msg}")
        self.last_order_msg = msg

kiwoom = None

def start_kiwoom_server():
    # QApplication 및 KiwoomAPI를 메인 스레드에서 실행
    global kiwoom  # 전역 변수 사용
    db_pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        host="project-db-cgi.smhrd.com",
        user="mp_24K_DCX13_p3_2",
        password="smhrd2",
        database="mp_24K_DCX13_p3_2",
        port=3307,
        ssl_disabled=True
    )

    app = QApplication([])  # QApplication은 반드시 메인 스레드에서 실행
    kiwoom = KiwoomAPI(db_pool)  # 전역 객체로 초기화
    kiwoom.login()

    while not kiwoom.connected:
        print("로그인 중")
        app.processEvents()

    kiwoom.fetch_stock_list()
    stock_codes = [code for code, _ in kiwoom.stock_list]
    kiwoom.request_real_data("1000", ";".join(stock_codes), "10")

    threading.Thread(target=periodic_save_real_data, args=(kiwoom,), daemon=True).start()
    threading.Thread(target=periodic_save_daily_data, args=(kiwoom,), daemon=True).start()

    app.exec_()

class TradeRequest(BaseModel):
    stock_code: str  # 종목코드
    quantity: int    # 주문 수량
    price: int       # 주문 가격

def periodic_save_real_data(kiwoom, interval=5):
    # 실시간 데이터를 주기적으로 저장
    while not stop_event.is_set():  # stop_event가 set() 되면 루프 종료
        time.sleep(interval)
        if not kiwoom.real_data:
            print("실시간 데이터가 없음 저장 안함")
            continue

        print("실시간 데이터 체크 중.")
        try:
            connection = kiwoom.db_pool.get_connection()
            cursor = connection.cursor()

            query = """
            INSERT INTO realtime_stocks (stock_idx, current_price, create_at)
            VALUES (%s, %s, NOW())
            """
            values = [(code, info["current_price"]) for code, info in kiwoom.real_data.items()]
            cursor.executemany(query, values)
            connection.commit()

            print(f"실시간 데이터 저장 완료: {len(values)}")
        except Error as err:
            print(f"[ERROR] Database error: {err}")
        finally:
            cursor.close()
            connection.close()


def periodic_save_daily_data(kiwoom):
    # 일봉 데이터를 매일 저장
    while not stop_event.is_set():  # stop_event가 set() 되면 루프 종료
        now = datetime.datetime.now()
        if now.hour == 15 and now.minute == 55:  # 매일 16:00에 저장
            print("일봉 데이터 저장 중")
            kiwoom.fetch_stock_list()
            stock_list = kiwoom.stock_list
            if not stock_list:
                print("[WARNING] 종목 리스트가 비어 있음!")
                return

            kiwoom.start_stock_requests(stock_list)

        time.sleep(60)  # 1분 대기

@app.post("/trade/buy")
async def buy_stock(request: TradeRequest):
    # 매수 요청 처리
    if not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API is not connected.")

    try:
        result = kiwoom.send_order("BUY", request.stock_code, request.quantity, request.price)
        return {"status": "pending", "message": "매수 요청이 전송되었습니다.", "result_code": result}
    except Exception as e:
        print(f"[ERROR] 매수 요청 실패: {e}")
        return {"status": "failure", "message": f"매수 요청 중 오류 발생: {e}"}


@app.post("/trade/sell")
async def sell_stock(request: TradeRequest):
    # 매도 요청 처리
    if not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API is not connected.")

    try:
        result = kiwoom.send_order("SELL", request.stock_code, request.quantity, request.price)
        return {"status": "pending", "message": "매도 요청이 전송되었습니다.", "result_code": result}
    except Exception as e:
        print(f"[ERROR] 매도 요청 실패: {e}")
        return {"status": "failure", "message": f"매도 요청 중 오류 발생: {e}"}

@app.get("/account/holdings")
async def get_holdings():
    # 보유 종목 조회
    global kiwoom
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API is not connected.")

    print("[DEBUG] FastAPI received request for holdings!")
    
    # 🔹 이벤트 초기화 (이전 요청으로 인해 set() 되어 있을 수 있음)
    holdings_response_event.clear()
    
    kiwoom.request_holdings()

    # 🔹 데이터가 올 때까지 최대 5초 동안 기다림
    try:
        await asyncio.wait_for(holdings_response_event.wait(), timeout=5)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Holdings data request timed out.")

    return JSONResponse(content={"status": "success", "data": kiwoom.holdings_data})

@app.get("/account/trade-history")
async def get_trade_history():
    # 거래 내역 조회
    global kiwoom
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API is not connected.")

    print("거래 내역 조회 실행!")

    # 🔹 이벤트 초기화
    trade_history_response_event.clear()

    kiwoom.request_trade_history()

    # 🔹 데이터가 올 때까지 최대 5초 동안 기다림
    try:
        await asyncio.wait_for(trade_history_response_event.wait(), timeout=5)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Trade history request timed out.")

    return JSONResponse(content={"status": "success", "data": kiwoom.trade_history_data})

@app.get("/account/info")
async def get_account_info():
    # 키움 API에서 계좌 정보를 요청하고 반환
    global kiwoom
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API is not connected.")

    print("[DEBUG] FastAPI received request for account info!")

    # 🔹 이벤트 초기화
    account_response_event.clear()
    pending_orders_response_event.clear()

    # 🔹 키움 API에 계좌 정보 & 미체결 내역 요청
    kiwoom.request_account_info()
    kiwoom.request_pending_orders()

    # 🔹 데이터가 올 때까지 최대 5초 동안 기다림
    try:
        await asyncio.wait_for(account_response_event.wait(), timeout=5)
        await asyncio.wait_for(pending_orders_response_event.wait(), timeout=5)
    except asyncio.TimeoutError:
        print("[ERROR] Account info request timed out.")
        raise HTTPException(status_code=408, detail="Account info request timed out.")

    print("[INFO] Sending account info & pending orders to main server:")
    print("Account Info:", kiwoom.account_info)
    print("Pending Orders:", kiwoom.pending_orders_data)

    return JSONResponse(content={
        "status": "success",
        "account_info": kiwoom.account_info,
        "pending_orders": kiwoom.pending_orders_data
    })

class CancelOrderRequest(BaseModel):
    order_number: str  # 반드시 문자열로 처리

@app.post("/account/cancel-order")
async def cancel_order(request: CancelOrderRequest):
    # 키움 API를 통해 미체결 주문 취소
    order_number = request.order_number
    global kiwoom
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API가 연결되지 않았습니다.")

    print(f"[DEBUG] 주문 취소 요청 수신: {order_number}")

    try:
        result = kiwoom.cancel_order(order_number)
        return {"status": "success", "message": "주문 취소 요청 완료", "result_code": result}
    except Exception as e:
        print(f"[ERROR] 주문 취소 실패: {e}")
        return {"status": "failure", "message": f"주문 취소 중 오류 발생: {e}"}

@app.on_event("startup")
def startup_event():
    """
    FastAPI 서버 시작 시 실행
    """
    global stop_event
    stop_event.clear()  # 서버 시작 시 stop_event 초기화
    threading.Thread(target=start_kiwoom_server, daemon=True).start()

@app.on_event("shutdown")
def shutdown_event():
    """
    FastAPI 서버 종료 시 실행
    """
    global stop_event
    stop_event.set()  # 모든 스레드 종료 신호
    print("[INFO] Shutting down Kiwoom server and stopping all threads.")
    