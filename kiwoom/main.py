import asyncio
import datetime
import logging
import queue
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from mysql.connector import Error, pooling
from pydantic import BaseModel
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtWidgets import QApplication

def safe_int(raw_value, default=0):
    try:
        value = raw_value.strip()
        if value == "":
            return default
        return int(value)
    except Exception:
        return default


# ─────────────────────────────────────────────
# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ─────────────────────────────────────────────
# FastAPI 인스턴스 생성
app = FastAPI()

# 전역 이벤트(비동기 응답 대기용)
stop_event = threading.Event()
holdings_response_event = asyncio.Event()         # 보유 종목 이벤트
trade_history_response_event = asyncio.Event()      # 거래 내역 이벤트
account_response_event = asyncio.Event()            # 계좌 정보 이벤트
pending_orders_response_event = asyncio.Event()     # 미체결 내역 이벤트

# ─────────────────────────────────────────────
# API 요청 큐 (Kiwoom API 관련 TR 요청은 모두 이 큐를 통해 순차적으로 실행)
api_request_queue = queue.Queue()

# ─────────────────────────────────────────────
# 헬퍼 함수
def clean_price(raw_price: str) -> int:
    try:
        return abs(int(raw_price))
    except ValueError:
        logging.error(f"Invalid price format: {raw_price}")
        return 0

# ─────────────────────────────────────────────
# 장이 열려있는지 여부를 판별하는 함수
def is_holiday(date):
    # 현재는 placeholder 함수입니다.
    # 실제 공휴일 정보를 기반으로 구현하세요.
    return False

def market_is_open():
    now = datetime.datetime.now()
    # 주말 체크 (토요일:5, 일요일:6)
    if now.weekday() >= 5:
        return False
    # 오후 3시 30분 이후라면
    if now.hour > 15 or (now.hour == 15 and now.minute > 30):
        return False
    # 공휴일 체크
    if is_holiday(now.date()):
        return False
    return True

# ─────────────────────────────────────────────
# Kiwoom API 클래스
class KiwoomAPI(QAxWidget):
    REAL_SCREEN_NO = "1000"
    ORDER_SCREEN_NO = "1001"
    
    def __init__(self, db_pool):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.db_pool = db_pool

        # 로그인 및 내부 플래그
        self.login_event_loop = QEventLoop()
        self.connected = False
        self.request_in_progress = False  # 현재 TR 요청 진행 여부

        # 데이터 저장 변수
        self.real_data = {}           # 실시간 데이터
        self.data = []                # 일봉 데이터
        self.holdings_data = []       # 보유 종목
        self.trade_history_data = []  # 거래 내역
        self.stock_list = []          # 종목 리스트 (DB)
        self.account_info = {}        # 계좌 정보
        self.pending_orders_data = [] # 미체결 내역
        self.current_stock = None
        self.account_no = None

        # 이벤트 연결 (OpenAPI 이벤트)
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveTrData.connect(self._on_receive_trdata)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveMsg.connect(self._on_receive_msg)

        # ── 요청 큐 처리용 QTimer (Kiwoom API가 실행되는 스레드의 이벤트 루프에서 주기적으로 큐 확인)
        self.api_queue_timer = QTimer(self)
        self.api_queue_timer.timeout.connect(self.process_api_queue)
        self.api_queue_timer.start(100)  # 100ms 간격으로 큐 확인

    def process_api_queue(self):
        # 큐에 대기 중인 요청이 있고 현재 요청 진행 중이 아니면 하나 실행
        if not self.request_in_progress and not api_request_queue.empty():
            req_func = api_request_queue.get()
            self.request_in_progress = True
            logging.debug("API 요청 큐에서 요청 실행")
            req_func()

    def schedule_request(self, req_callable):
        # TR 요청을 큐에 등록
        api_request_queue.put(req_callable)

    def _mark_request_complete(self):
        # TR 요청이 완료되었음을 표시하여 다음 요청을 실행할 수 있도록 함
        self.request_in_progress = False
        logging.debug("TR 요청 완료; 다음 요청 가능")

    # ─────────────────────────────────────────────
    # 로그인 및 계좌 관련
    def login(self):
        logging.debug("로그인 시도 중...")
        self.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def _on_event_connect(self, err_code):
        if err_code == 0:
            logging.debug("로그인 성공!")
            self.connected = True
            raw_acc = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            self.account_no = raw_acc.strip().split(';')[0]
            logging.debug(f"사용 계좌번호: {self.account_no}")
        else:
            logging.error(f"로그인 실패 - 에러 코드: {err_code}")
        self.login_event_loop.exit()

    # ─────────────────────────────────────────────
    # TR 요청 메서드 (내부 do_request 함수로 실제 API 호출)
    def request_holdings(self):
        if not self.account_no:
            logging.error("계좌번호가 없습니다.")
            return

        logging.debug("보유 종목 조회 요청 준비 중...")
        self.holdings_data = []  # 기존 데이터 초기화

        def do_request():
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "4")
            self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "4")
            self.dynamicCall("CommRqData(QString, QString, int, QString)",
                             "계좌평가잔고내역조회", "opw00018", 0, "9001")
        self.schedule_request(do_request)

    def request_trade_history(self):
        # 기존 데이터 초기화 (누적)
        self.trade_history_data.clear()
        # 최근 7일(오늘 포함)의 주문일자를 생성 (예: 오늘, 어제, ...)
        for i in range(7):
            order_date = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y%m%d")
            logging.debug(f"OPW00007 요청 - 주문일자: {order_date}")

            self.last_requested_date = order_date
            
            def do_request(date=order_date):
                self.dynamicCall("SetInputValue(QString, QString)", "주문일자", date)
                self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
                self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
                self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
                self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "4")       # 체결내역만
                self.dynamicCall("SetInputValue(QString, QString)", "주식채권구분", "1")    # 주식
                self.dynamicCall("SetInputValue(QString, QString)", "매도수구분", "0")        # 전체 (매도/매수 모두)
                result = self.dynamicCall("CommRqData(QString, QString, int, QString)",
                                          "계좌별주문체결내역상세요청", "opw00007", 0, "9002")
                logging.debug(f"OPW00007 요청 결과 (주문일자 {date}): {result}")
                if result != 0:
                    logging.error(f"OPW00007 요청 실패 (주문일자 {date}, 에러 코드: {result})")
            self.schedule_request(do_request)
            
            # 각 날짜별 응답을 대기 (최대 5초)
            start_wait = time.time()
            while not trade_history_response_event.is_set() and time.time() - start_wait < 5:
                time.sleep(0.5)
            # 응답 대기가 끝나면 이벤트 플래그 초기화하고 다음 날짜 요청 진행
            trade_history_response_event.clear()
        trade_history_response_event.set()


    def request_account_info(self):
        if not self.account_no:
            logging.error("계좌번호가 없습니다.")
            return

        logging.debug("계좌 정보 요청 준비 중...")
        self.account_info = {}

        def do_request():
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("CommRqData(QString, QString, int, QString)",
                             "예수금상세현황", "opw00001", 0, "9003")
        self.schedule_request(do_request)

    def request_pending_orders(self):
        if not self.account_no:
            logging.error("계좌 정보가 없습니다.")
            return

        logging.debug("미체결 내역 요청 준비 중...")
        self.pending_orders_data = []

        def do_request():
            self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_no)
            self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
            self.dynamicCall("CommRqData(QString, QString, int, QString)",
                             "미체결내역조회", "opt10075", 0, "9004")
        self.schedule_request(do_request)

    def request_stock_data(self, stock_code, stock_name):
        logging.info(f"{stock_name} ({stock_code}) - 일봉 데이터 요청 준비 중")
        self.data.clear()
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y%m%d")

        def do_request():
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", end_date)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            result = self.dynamicCall("CommRqData(QString, QString, int, QString)",
                                      "주식일봉차트조회", "opt10081", 0, "0101")
            if result != 0:
                logging.error(f"일봉 데이터 요청 실패 (오류 코드: {result})")
                QTimer.singleShot(60000, self.process_next_stock)
        self.schedule_request(do_request)

    def send_order(self, trade_type, stock_code, quantity, price):
        order_type = 1 if trade_type == "BUY" else 2  # 1: 매수, 2: 매도
        result_container = {}

        def do_send():
            res = self.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                [
                    f"{trade_type}주문",
                    self.ORDER_SCREEN_NO,
                    self.account_no,
                    order_type,
                    stock_code,
                    quantity,
                    price,
                    "00",
                    ""
                ]
            )
            result_container["result"] = res
            logging.info(f"{trade_type} 요청 완료 - 종목: {stock_code}, 수량: {quantity}, 가격: {price}")
        self.schedule_request(do_send)

        wait_start = time.time()
        while "result" not in result_container and time.time() - wait_start < 5:
            time.sleep(0.1)
        return result_container.get("result", -1)

    # ─────────────────────────────────────────────
    # 실시간 데이터 요청 및 이벤트 처리
    def request_real_data(self, screen_no, codes, fid_list):
        try:
            logging.debug(f"실시간 데이터 요청: {codes}")
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, codes, fid_list, "0")
            logging.debug(f"실시간 데이터 요청 성공: {codes}")
        except Exception as e:
            logging.error(f"실시간 데이터 요청 실패: {e}")

    def _on_receive_real_data(self, code, real_type, data):
        if real_type == "주식체결":
            raw_price = self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            current_price = clean_price(raw_price)
            if current_price > 0:
                self.real_data[code] = {"current_price": current_price}

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        logging.info(f"키움 API 메시지: {msg}")
        self.last_order_msg = msg
        # 주문 관련 메시지인 경우 _mark_request_complete() 호출
        if "주문" in rqname:
            self._mark_request_complete()

    def _on_receive_trdata(self, screen_no, rqname, trcode, record_name, prev_next, data_len, err_code, msg, sRQName):
        if rqname == "주식일봉차트조회":
            # 기존 일봉 데이터 처리 코드 (생략)
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(cnt):
                record = {
                    "date": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "일자").strip(),
                    "open": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "시가").strip()),
                    "high": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "고가").strip()),
                    "low": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "저가").strip()),
                    "close": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()),
                    "volume": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip())
                }
                self.data.append(record)
            self.save_to_db()
            QTimer.singleShot(3000, self.process_next_stock)
            self._mark_request_complete()

        elif rqname == "계좌평가잔고내역조회":
            # 기존 보유 종목 처리 코드 (생략)
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(cnt):
                holding = {
                    "stock_name": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip(),
                    "current_price": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()),
                    "buy_price": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입가").strip()),
                    "quantity": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량").strip()),
                    "evaluation_profit": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "평가손익").strip())
                }
                self.holdings_data.append(holding)
            logging.debug(f"보유 종목 데이터: {self.holdings_data}")
            holdings_response_event.set()
            self._mark_request_complete()

        elif rqname == "계좌별주문체결내역상세요청":
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            logging.debug(f"계좌별주문체결내역상세요청 응답 건수: {cnt}")
            for i in range(cnt):
                try:
                    trade = {
                        "order_date": self.last_requested_date,
                        "stock_name": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip(),
                        "price": safe_int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결단가")),
                        "quantity": safe_int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "체결수량")),
                        "type": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문구분").strip()
                    }
                except Exception as e:
                    logging.error(f"계좌별주문체결내역상세요청 데이터 파싱 에러: {e}")
                    continue
                self.trade_history_data.append(trade)
            logging.debug(f"조회된 체결내역 데이터 건수: {len(self.trade_history_data)}")
            logging.debug(f"조회된 체결내역 데이터: {self.trade_history_data}")
            if prev_next == "2":
                logging.debug("추가 데이터가 있습니다. 다음 페이지 요청 중...")
                self.request_trade_history(prev_next="2")
            else:
                trade_history_response_event.set()
            self._mark_request_complete()

        elif rqname == "예수금상세현황":
            # 기존 계좌 정보 처리 코드 (생략)
            예수금 = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "예수금").strip())
            출금가능금액 = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "출금가능금액").strip())
            주문가능금액 = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "주문가능금액").strip())
            self.account_info = {
                "account_number": self.account_no,
                "balance": 예수금,
                "available_withdraw": 출금가능금액,
                "order_available": 주문가능금액
            }
            logging.debug(f"계좌 정보: {self.account_info}")
            account_response_event.set()
            self._mark_request_complete()

        elif rqname == "미체결내역조회":
            # 기존 미체결 내역 처리 코드 (생략)
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(cnt):
                order = {
                    "order_no": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문번호").strip(),
                    "date": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문시간").strip(),
                    "stock_name": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip(),
                    "price": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문가격").strip()),
                    "quantity": int(self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문수량").strip()),
                    "status": self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문상태").strip()
                }
                self.pending_orders_data.append(order)
            pending_orders_response_event.set()
            self._mark_request_complete()


    def save_to_db(self):
        if not self.current_stock:
            logging.warning("저장할 주식 데이터가 없습니다.")
            return

        stock_code, _ = self.current_stock
        try:
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()
            delete_query = "DELETE FROM stock_datas WHERE stock_idx = %s"
            cursor.execute(delete_query, (stock_code,))
            insert_query = """
                INSERT INTO stock_datas 
                (stock_idx, stock_date, open_price, highest_price, lowest_price, close_price, trade_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            insert_values = [
                (stock_code, rec["date"], rec["open"], rec["high"], rec["low"], rec["close"], rec["volume"])
                for rec in self.data
            ]
            cursor.executemany(insert_query, insert_values)
            connection.commit()
            logging.info(f"{stock_code} 종목 데이터 {len(insert_values)} 건 저장 완료.")
        except Error as err:
            logging.error(f"DB 저장 에러: {err}")
        finally:
            cursor.close()
            connection.close()

    def fetch_stock_list(self):
        logging.debug("DB에서 종목 리스트 조회 중...")
        try:
            connection = self.db_pool.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT stock_idx, stock_name FROM stocks")
            self.stock_list = cursor.fetchall()
            logging.debug(f"DB에서 받은 종목 데이터: {self.stock_list}")
        except Error as err:
            logging.error(f"DB 에러: {err}")
        finally:
            cursor.close()
            connection.close()

    def start_stock_requests(self, stock_list):
        self.stock_list = stock_list.copy()
        self.process_next_stock()

    def process_next_stock(self):
        if not self.stock_list:
            logging.info("모든 종목 데이터 처리 완료.")
            return
        self.current_stock = self.stock_list.pop(0)
        stock_code, stock_name = self.current_stock
        logging.info(f"{stock_name} ({stock_code}) 데이터 요청 중...")
        self.request_stock_data(stock_code, stock_name)

# ─────────────────────────────────────────────
# 백그라운드에서 Kiwoom API 서버 시작
kiwoom = None

def start_kiwoom_server():
    global kiwoom
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
    qt_app = QApplication([])
    kiwoom = KiwoomAPI(db_pool)
    kiwoom.login()

    while not kiwoom.connected:
        logging.debug("로그인 대기 중...")
        qt_app.processEvents()

    kiwoom.fetch_stock_list()
    stock_codes = [code for code, _ in kiwoom.stock_list]
    kiwoom.request_real_data(KiwoomAPI.REAL_SCREEN_NO, ";".join(stock_codes), "10")

    threading.Thread(target=periodic_save_real_data, args=(kiwoom,), daemon=True).start()
    threading.Thread(target=periodic_save_daily_data, args=(kiwoom,), daemon=True).start()

    qt_app.exec_()

def periodic_save_real_data(kiwoom_instance, interval=5):
    while not stop_event.is_set():
        time.sleep(interval)
        # 장이 열려있는지 확인 (오후 3:30 이전, 평일, 공휴일 아님)
        if not market_is_open():
            logging.debug("장 시간 외입니다. 실시간 데이터 저장 건너뜀.")
            continue
        if not kiwoom_instance.real_data:
            logging.debug("실시간 데이터 없음. 저장 건너뜀.")
            continue
        logging.debug("실시간 데이터 저장 시도 중.")
        try:
            connection = kiwoom_instance.db_pool.get_connection()
            cursor = connection.cursor()
            query = """
                INSERT INTO realtime_stocks (stock_idx, current_price, create_at)
                VALUES (%s, %s, NOW())
            """
            values = [(code, info["current_price"]) for code, info in kiwoom_instance.real_data.items()]
            cursor.executemany(query, values)
            connection.commit()
            logging.info(f"실시간 데이터 저장 완료: {len(values)} 건")
        except Error as err:
            logging.error(f"실시간 DB 저장 에러: {err}")
        finally:
            cursor.close()
            connection.close()

def periodic_save_daily_data(kiwoom_instance):
    while not stop_event.is_set():
        now = datetime.datetime.now()
        if now.hour == 15 and now.minute == 50:
            logging.info("일봉 데이터 저장 시작")
            kiwoom_instance.fetch_stock_list()
            if not kiwoom_instance.stock_list:
                logging.warning("종목 리스트가 비어 있습니다.")
            else:
                kiwoom_instance.start_stock_requests(kiwoom_instance.stock_list)
        time.sleep(60)

# 추가: 시장 개장 여부 판단 함수
def is_holiday(date):
    # 여기는 실제 공휴일 정보를 반영하는 로직으로 교체해야 합니다.
    return False

def market_is_open():
    now = datetime.datetime.now()
    # 주말 (토요일=5, 일요일=6)인 경우
    if now.weekday() >= 5:
        return False
    # 오후 3시 30분 이후인 경우
    if now.hour > 15 or (now.hour == 15 and now.minute > 30):
        return False
    # 공휴일인 경우
    if is_holiday(now.date()):
        return False
    return True

# ─────────────────────────────────────────────
# FastAPI 요청 모델 및 엔드포인트
class TradeRequest(BaseModel):
    stock_code: str
    quantity: int
    price: int

@app.post("/trade/buy")
async def buy_stock(request: TradeRequest):
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API가 연결되어 있지 않습니다.")
    try:
        result = kiwoom.send_order("BUY", request.stock_code, request.quantity, request.price)
        return {"status": "pending", "message": "매수 요청 전송", "result_code": result}
    except Exception as e:
        logging.error(f"매수 요청 오류: {e}")
        return {"status": "failure", "message": f"매수 요청 중 오류: {e}"}

@app.post("/trade/sell")
async def sell_stock(request: TradeRequest):
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API가 연결되어 있지 않습니다.")
    try:
        result = kiwoom.send_order("SELL", request.stock_code, request.quantity, request.price)
        return {"status": "pending", "message": "매도 요청 전송", "result_code": result}
    except Exception as e:
        logging.error(f"매도 요청 오류: {e}")
        return {"status": "failure", "message": f"매도 요청 중 오류: {e}"}

@app.get("/account/holdings")
async def get_holdings():
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API가 연결되어 있지 않습니다.")
    logging.debug("FastAPI: 보유 종목 요청 수신")
    holdings_response_event.clear()
    kiwoom.request_holdings()
    try:
        await asyncio.wait_for(holdings_response_event.wait(), timeout=5)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="보유 종목 조회 시간 초과")
    return JSONResponse(content={"status": "success", "data": kiwoom.holdings_data})

@app.get("/account/trade-history")
async def get_trade_history():
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API가 연결되어 있지 않습니다.")
    logging.debug("FastAPI: 거래 내역 요청 수신")
    trade_history_response_event.clear()
    kiwoom.request_trade_history()
    try:
        await asyncio.wait_for(trade_history_response_event.wait(), timeout=10)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="거래 내역 조회 시간 초과")
    return JSONResponse(content={"status": "success", "data": kiwoom.trade_history_data})

@app.get("/account/info")
async def get_account_info():
    if not kiwoom or not kiwoom.connected:
        raise HTTPException(status_code=400, detail="Kiwoom API가 연결되어 있지 않습니다.")
    logging.debug("FastAPI: 계좌 정보 요청 수신")
    account_response_event.clear()
    pending_orders_response_event.clear()
    kiwoom.request_account_info()
    kiwoom.request_pending_orders()
    try:
        await asyncio.wait_for(account_response_event.wait(), timeout=5)
        await asyncio.wait_for(pending_orders_response_event.wait(), timeout=5)
    except asyncio.TimeoutError:
        logging.error("계좌 정보 조회 시간 초과")
        raise HTTPException(status_code=408, detail="계좌 정보 조회 시간 초과")
    return JSONResponse(content={
        "status": "success",
        "account_info": kiwoom.account_info,
        "pending_orders": kiwoom.pending_orders_data
    })

# ─────────────────────────────────────────────
# FastAPI 서버 시작/종료 이벤트
@app.on_event("startup")
def startup_event():
    stop_event.clear()
    threading.Thread(target=start_kiwoom_server, daemon=True).start()

@app.on_event("shutdown")
def shutdown_event():
    stop_event.set()
    logging.info("서버 종료 - Kiwoom API 및 모든 스레드 중지")
