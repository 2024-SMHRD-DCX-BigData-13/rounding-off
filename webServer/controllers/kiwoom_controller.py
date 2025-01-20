# main_server.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
import httpx
import asyncio
import websockets

router = APIRouter()

# # 실시간 데이터 WebSocket 연결
# KIWOOM_API_URL = "http://127.0.0.1:8001"

# # 주기적으로 데이터를 가져오는 작업
# async def fetch_real_time_data(stock_code: str):
#     while True:
#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(f"{KIWOOM_API_URL}/real-data/{stock_code}")
#                 if response.status_code == 200:
#                     data = response.json()
#                     print(f"실시간 데이터 수신 ({stock_code}): {data}")
#                 else:
#                     print(f"키움 API 서버에서 데이터 수신 실패: {response.status_code}")
#         except httpx.RequestError as exc:
#             print(f"HTTP 요청 중 오류 발생: {exc}")
#         await asyncio.sleep(1)  # 1초마다 데이터 요청

# # 서버 시작 시 실시간 데이터 요청 작업 시작
# @router.on_event("startup")
# async def startup_event():
#     stock_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
#     for stock_code in stock_codes:
#         asyncio.create_task(fetch_real_time_data(stock_code))

# # @router.get("/")
# # async def root():
# #     return {"message": "메인 서버 실행 중, 실시간 데이터 수신 중"}

# HTML 템플릿
# html_content = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>실시간 데이터</title>
#     <script>
#         const socket = new WebSocket("ws://127.0.0.1:8001/ws");
#         socket.onmessage = function(event) {
#             const data = JSON.parse(event.data);
#             document.getElementById("price").innerText = "가격: " + data.price;
#             document.getElementById("volume").innerText = "거래량: " + data.volume;
#         };
#         socket.onclose = function() {
#             console.log("WebSocket 연결 종료");
#         };
#     </script>
# </head>
# <body>
#     <h1>실시간 데이터</h1>
#     <p id="price">가격: </p>
#     <p id="volume">거래량: </p>
# </body>
# </html>
# """

# @router.get("/mmm", response_class=HTMLResponse)
# async def root():
#     """
#     메인 페이지 HTML 반환
#     """
#     return html_content

# async def receive_data_from_kiwoom():
#     """
#     키움 API 서버와 WebSocket 연결
#     """
#     uri = "ws://127.0.0.1:8001/ws"
#     async with websockets.connect(uri) as websocket:
#         while True:
#             try:
#                 data = await websocket.recv()
#                 print(f"키움 서버 데이터 수신: {data}")
#                 # 클라이언트로 전송 (필요 시 WebSocket 클라이언트 추가 구현 가능)
#             except websockets.ConnectionClosed:
#                 print("키움 서버 WebSocket 연결 종료")
#                 break

# @router.on_event("startup")
# async def startup_event():
#     """
#     서버 시작 시 키움 API WebSocket 연결 시작
#     """
#     asyncio.create_task(receive_data_from_kiwoom())

from fastapi import APIRouter, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.logger import logger
import httpx


router = APIRouter()

templates = Jinja2Templates(directory="views")

# 서브 서버 URL 설정
SUB_SERVER_URL = "http://127.0.0.1:8001/fetch-daily-data"

@router.get("/client")
async def client(request: Request):
    # /templates/client.html파일을 response함
    return templates.TemplateResponse("client.html", {"request":request})

# 웹소켓 설정 ws://127.0.0.1:8000/ws 로 접속할 수 있음
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(f"client connected : {websocket.client}")
    await websocket.accept() # client의 websocket접속 허용
    await websocket.send_text(f"Welcome client : {websocket.client}")
    while True:
        data = await websocket.receive_text()  # client 메시지 수신대기
        print(f"message received : {data} from : {websocket.client}")
        await websocket.send_text(f"Message text was: {data}") # client에 메시지 전달
