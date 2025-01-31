from fastapi import *
from fastapi.responses import *
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
import mysql.connector
import random
from typing import List
from pydantic import BaseModel
import requests
import time
import httpx

router = APIRouter()

templates = Jinja2Templates(directory="views")

# 서브 서버 URL 설정
SUB_SERVER_URL = "http://127.0.0.1:8001"

class OrderRequest(BaseModel):
    stock_id: str    # 종목코드
    quantity: int    # 주문 수량
    price: int       # 주문 가격
    trade_type: str  # 주문 유형 (BUY or SELL)

print(OrderRequest)

@router.post("/trade/order")
async def trade_order(request: OrderRequest):
    """
    주문 요청 처리 - 서브 서버로 요청 전송
    """
    print("[DEBUG] Received OrderRequest:", request.dict())  # 요청 데이터 출력

    try:
        # 서브 서버로 주문 요청 전송
        async with httpx.AsyncClient() as client:
            sub_server_response = await client.post(
                f"{SUB_SERVER_URL}/trade/{request.trade_type.lower()}",
                json={
                    "stock_code": request.stock_id,
                    "quantity": request.quantity,
                    "price": request.price,
                }
            )

        # 서브 서버 응답 확인
        if sub_server_response.status_code == 200:
            return sub_server_response.json()  # 응답 그대로 반환
        else:
            raise HTTPException(
                status_code=sub_server_response.status_code,
                detail=f"서브 서버 요청 실패: {sub_server_response.text}"
            )

    except Exception as e:
        print(f"[ERROR] 서브 서버와의 통신 실패: {e}")
        raise HTTPException(status_code=500, detail="주문 처리 중 오류가 발생했습니다.")


@router.get("/account/holdings")
async def get_holdings():
    """
    클라이언트 → 메인 서버 요청 → 서브 서버 요청 → 응답 반환
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SUB_SERVER_URL}/account/holdings")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail="서브 서버 요청 실패")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서브 서버와의 통신 오류: {e}")

@router.get("/account/trade-history")
async def get_trade_history():
    """
    클라이언트 → 메인 서버 요청 → 서브 서버 요청 → 응답 반환
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SUB_SERVER_URL}/account/trade-history")
        
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail="서브 서버 요청 실패")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서브 서버와의 통신 오류: {e}")

@router.get("/account/info")
async def get_account_info():
    """
    ✅ 메인 서버 컨트롤러
    클라이언트 → 메인 서버 요청 → 서브 서버 요청 → 응답 반환
    """
    try:
        async with httpx.AsyncClient() as client:
            # 🔹 서브 서버에 계좌 정보 요청
            response_account = await client.get(f"{SUB_SERVER_URL}/account/info")
            if response_account.status_code != 200:
                raise HTTPException(status_code=response_account.status_code, detail="계좌 정보 요청 실패")

            # 🔹 서브 서버에 실시간 미체결 내역 요청
            response_pending = await client.get(f"{SUB_SERVER_URL}/account/pending-orders")
            if response_pending.status_code != 200:
                raise HTTPException(status_code=response_pending.status_code, detail="미체결 내역 요청 실패")

        # 🔹 JSON 데이터 변환
        account_data = response_account.json()
        pending_orders = response_pending.json()

        return {
            "status": "success",
            "account_info": account_data["account_info"],
            "pending_orders": pending_orders["data"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서브 서버와의 통신 오류: {e}")