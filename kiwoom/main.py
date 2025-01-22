import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from kiwoom_api import KiwoomAPI
import mysql.connector
from PyQt5.QtWidgets import QApplication

# Kiwoom 객체 초기화
kiwoom = None

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """POST 요청 처리"""
        if self.path == "/real-time-data":
            self.handle_real_time_data()
        elif self.path == "/historical-data":
            self.handle_historical_data()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_real_time_data(self):
        """실시간 데이터 요청 처리"""
        try:
            stock_codes = ";".join([code for code, _ in kiwoom.stock_list])
            kiwoom.request_real_data("1000", stock_codes, "10")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Real-time data started successfully")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Failed to start real-time data: {e}".encode())

    def handle_historical_data(self):
        """과거 데이터 요청 처리"""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = json.loads(self.rfile.read(content_length))
            stock_code = post_data.get("stock_code")
            start_date = post_data.get("start_date")
            end_date = post_data.get("end_date")

            kiwoom.request_historical_data(stock_code, start_date, end_date)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Historical data request sent successfully")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Failed to request historical data: {e}".encode())

def initialize_kiwoom():
    """Kiwoom API 초기화"""
    global kiwoom
    app_instance = QApplication([])
    db_connection = mysql.connector.connect(
        host="project-db-cgi.smhrd.com",
        user="mp_24K_DCX13_p3_2",
        password="smhrd2",
        database="mp_24K_DCX13_p3_2",
        port=3307
    )
    kiwoom = KiwoomAPI(db_connection)

    # 로그인 처리
    kiwoom.login()
    while not kiwoom.connected:
        app_instance.processEvents()

    print("[INFO] Kiwoom API initialized. Starting HTTP server...")

    # HTTP 서버 실행
    server = HTTPServer(("0.0.0.0", 5000), RequestHandler)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # PyQt5 이벤트 루프 실행
    app_instance.exec_()

if __name__ == "__main__":
    initialize_kiwoom()
