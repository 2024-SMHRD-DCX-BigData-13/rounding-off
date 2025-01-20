import asyncio
import websockets
import pythoncom
import win32com.client
import mysql.connector


class KiwoomEventHandler:
    """
    키움 OpenAPI 이벤트 핸들러
    """
    def __init__(self, parent):
        self.parent = parent

    def OnEventConnect(self, err_code):
        if err_code == 0:
            print("로그인 성공")
            self.parent.connected = True
        else:
            print(f"로그인 실패: {err_code}")

    def OnReceiveRealData(self, code, real_type, real_data):
        """
        실시간 데이터 수신 이벤트
        """
        if real_type == "주식체결":  # 주식 체결 데이터
            current_price = self.parent.ocx.GetCommRealData(code, 10).strip()  # 현재가
            volume = self.parent.ocx.GetCommRealData(code, 15).strip()  # 거래량
            self.parent.real_data[code] = {
                "current_price": current_price,
                "volume": volume
            }


class KiwoomAPI:
    def __init__(self):
        self.ocx = win32com.client.Dispatch("KHOPENAPI.KHOpenAPICtrl.1")
        self.handler = KiwoomEventHandler(self)  # 이벤트 핸들러 연결
        self.connected = False
        self.real_data = {}

    def login(self):
        self.ocx.OnEventConnect = self.handler.OnEventConnect
        self.ocx.OnReceiveRealData = self.handler.OnReceiveRealData
        self.ocx.CommConnect()
        while not self.connected:
            pythoncom.PumpWaitingMessages()

    def set_real_data(self, screen_no, codes, fid_list):
        """
        실시간 데이터 요청 설정
        :param screen_no: 화면번호 (4자리 숫자)
        :param codes: 종목코드 리스트 (세미콜론으로 구분된 문자열)
        :param fid_list: 실시간 데이터 항목 리스트 (FIDs)
        """
        self.ocx.SetRealReg(screen_no, codes, fid_list, "0")
        print(f"실시간 데이터 요청 등록 - 코드들: {codes}, FID: {fid_list}")

    def disconnect_real_data(self, screen_no):
        self.ocx.DisconnectRealData(screen_no)
        print(f"실시간 데이터 연결 해제 - 화면번호: {screen_no}")


def fetch_stock_codes_from_db():
    """
    MySQL 데이터베이스에서 stocks 테이블의 stock_idx를 가져오는 함수
    :return: 종목코드 리스트 (세미콜론으로 연결된 문자열)
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",  # 데이터베이스 호스트
            user="com",  # 데이터베이스 사용자 이름
            password="com01",  # 데이터베이스 비밀번호
            database="books"  # 데이터베이스 이름
        )

        cursor = connection.cursor()
        cursor.execute("SELECT stock_idx FROM stocks")
        rows = cursor.fetchall()

        # 종목코드 리스트 생성
        codes = ";".join([row[0] for row in rows])
        return codes

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return ""

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


async def send_stock_data(websocket, path, kiwoom):
    """
    웹소켓을 통해 실시간 데이터를 전송하는 함수
    """
    try:
        while True:
            # 실시간 데이터 가져오기
            if kiwoom.real_data:
                for code, data in kiwoom.real_data.items():
                    message = {
                        "stock_code": code,
                        "current_price": data["current_price"],
                        "volume": data["volume"]
                    }
                    # 메시지 전송
                    await websocket.send(str(message))
                    print(f"Sent: {message}")

            # 1초 대기
            await asyncio.sleep(1)
    except websockets.ConnectionClosed:
        print("WebSocket connection closed.")


if __name__ == "__main__":
    # 키움 API 초기화 및 로그인
    kiwoom = KiwoomAPI()
    kiwoom.login()

    # MySQL에서 종목코드 가져오기
    stock_codes = fetch_stock_codes_from_db()

    if stock_codes:
        # 실시간 데이터 설정
        screen_no = "1000"
        fid_list = "10;15"  # 현재가(10), 거래량(15)
        kiwoom.set_real_data(screen_no, stock_codes, fid_list)

        # 웹소켓 서버 실행
        start_server = websockets.serve(lambda ws, path: send_stock_data(ws, path, kiwoom), "localhost", 8000)

        print("WebSocket server started at ws://localhost:8000")

        # 이벤트 루프 실행
        asyncio.get_event_loop().run_until_complete(start_server)

        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            kiwoom.disconnect_real_data(screen_no)
            print("프로그램 종료")
    else:
        print("종목 코드를 가져오지 못했습니다.")
