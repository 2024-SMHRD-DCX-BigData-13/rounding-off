# main_server.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import httpx
import asyncio

router = APIRouter()

# 실시간 데이터 WebSocket 연결
KIWOOM_API_URL = "http://127.0.0.1:8001"

# 주기적으로 데이터를 가져오는 작업
async def fetch_real_time_data(stock_code: str):
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{KIWOOM_API_URL}/real-data/{stock_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"실시간 데이터 수신 ({stock_code}): {data}")
                else:
                    print(f"키움 API 서버에서 데이터 수신 실패: {response.status_code}")
        except httpx.RequestError as exc:
            print(f"HTTP 요청 중 오류 발생: {exc}")
        await asyncio.sleep(1)  # 1초마다 데이터 요청

# 서버 시작 시 실시간 데이터 요청 작업 시작
@router.on_event("startup")
async def startup_event():
    stock_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    for stock_code in stock_codes:
        asyncio.create_task(fetch_real_time_data(stock_code))

# @router.get("/")
# async def root():
#     return {"message": "메인 서버 실행 중, 실시간 데이터 수신 중"}

