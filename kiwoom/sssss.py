from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
import sys

app = FastAPI()

class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnReceiveChejanData.connect(self.on_receive_chejan_data)
        self.OnReceiveMsg.connect(self.on_receive_msg)
        self.websocket = None  # 웹소켓 연결 객체
        self.connected = False

    def login(self):
        print("[INFO] Attempting to log in...")
        self.dynamicCall("CommConnect()")
        self.connected = True

    def send_order(self, order_type, account_no, stock_code, quantity, price, websocket):
        self.websocket = websocket  # 웹소켓 연결 객체 저장
        self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            ["Order", "0101", account_no, order_type, stock_code, quantity, price, "00", ""]
        )

    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """
        주문 체결 및 잔고 변동 이벤트
        """
        if gubun == "0":  # 주문 체결
            stock_code = self.dynamicCall("GetChejanData(int)", 9001).strip()  # 종목 코드
            trade_price = self.dynamicCall("GetChejanData(int)", 910).strip()  # 체결 가격
            trade_quantity = self.dynamicCall("GetChejanData(int)", 911).strip()  # 체결 수량
            trade_date = self.dynamicCall("GetChejanData(int)", 909).strip()  # 체결 일자

            # 주문 체결 결과 전송
            result = {
                "status": "buy" if int(self.dynamicCall("GetChejanData(int)", 905).strip()) == 2 else "sell",
                "stock_code": stock_code,
                "trade_price": int(trade_price),
                "trade_quantity": int(trade_quantity),
                "trade_date": trade_date
            }
            if self.websocket:
                self.websocket.send_json(result)

    def on_receive_msg(self, screen_no, rqname, trcode, msg):
        """
        주문 메시지 이벤트
        """
        if "성공" in msg:
            print("[INFO] Order successful:", msg)
        else:
            print("[ERROR] Order failed:", msg)
            if self.websocket:
                self.websocket.send_json({"status": "buy_fail" if "매수" in msg else "sell_fail"})


@app.websocket("/ws/order")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            stock_code = data.get("stock_code")
            quantity = data.get("quantity")
            price = data.get("price")
            order_type = data.get("order_type")  # 1 for sell, 2 for buy

            # Kiwoom API로 주문 실행
            kiwoom.send_order(order_type, account_no, stock_code, quantity, price, websocket)

    except WebSocketDisconnect:
        print("[INFO] WebSocket disconnected")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = KiwoomAPI()
    kiwoom.login()
    app.exec_()
