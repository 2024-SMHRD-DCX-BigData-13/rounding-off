import asyncio
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication
import websockets
import json
import threading
import mysql.connector
import sys

# 글로벌 KiwoomAPI 객체
kiwoom = None


class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.connected = False
        self.real_data = {}

        # 이벤트 연결
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveRealData.connect(self._on_receive_real_data)

    def login(self):
        print("[DEBUG] Attempting to log in...")
        self.dynamicCall("CommConnect()")

    def _on_event_connect(self, err_code):
        if err_code == 0:
            print("[DEBUG] Login successful!")
            self.connected = True
        else:
            print(f"[ERROR] Login failed with error code: {err_code}")

    def request_real_data(self, screen_no, codes, fid_list):
        print(f"[DEBUG] Requesting real-time data for codes: {codes}")
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_no, codes, fid_list, "0")

    def _on_receive_real_data(self, code, real_type, data):
        if real_type == "주식체결":
            current_price = self.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            volume = self.dynamicCall("GetCommRealData(QString, int)", code, 15).strip()
            self.real_data[code] = {
                "current_price": current_price,
                "volume": volume
            }
            print(f"[DEBUG] Data received: Code={code}, Price={current_price}, Volume={volume}")


def fetch_stock_codes_from_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="com",
            password="com01",
            database="books"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT stock_idx FROM stocks")
        rows = cursor.fetchall()
        if not rows:
            print("[ERROR] No stock codes found in the database.")
            return ""

        stock_codes = ";".join([row[0] for row in rows])
        print(f"[DEBUG] Loaded stock codes: {stock_codes}")
        return stock_codes
    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        return ""
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


async def send_real_data():
    global kiwoom
    uri = "ws://localhost:8000/ws"  # 메인 서버 웹소켓 URI
    try:
        async with websockets.connect(uri) as websocket:
            print("[DEBUG] Connected to main server.")
            while True:
                if kiwoom.real_data:
                    for code, data in kiwoom.real_data.items():
                        payload = json.dumps({
                            "stock_code": code,
                            "current_price": data["current_price"],
                            "volume": data["volume"]
                        })
                        await websocket.send(payload)
                        print(f"[DEBUG] Sent: {payload}")
                await asyncio.sleep(1)
    except Exception as e:
        print(f"[ERROR] WebSocket connection failed: {e}")


def start_kiwoom():
    global kiwoom
    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI()
    kiwoom.login()

    while not kiwoom.connected:
        app.processEvents()

    stock_codes = fetch_stock_codes_from_db()
    if not stock_codes:
        print("[ERROR] No stock codes available.")
        return

    screen_no = "1000"
    fid_list = "10;15"  # 현재가, 거래량
    kiwoom.request_real_data(screen_no, stock_codes, fid_list)

    print("[DEBUG] KiwoomManager started.")
    asyncio.run(send_real_data())  # asyncio 이벤트 루프 시작
    app.exec_()


if __name__ == "__main__":
    start_kiwoom()
