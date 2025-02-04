from fastapi import APIRouter, Form, HTTPException, Request ,Query
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
from models.getKiwoom import HttpClientModel
import mysql.connector
import random
from typing import List
from pydantic import BaseModel
import requests
import time
import httpx


# 주식 테이블 관련 기능 컨트롤러
router = APIRouter()

@router.get("/stocks")
def get_stocks():
    """
    FastAPI 엔드포인트: stocks 데이터를 데이터베이스에서 조회하고 JSON 형태로 반환
    """
    connection = None
    try:
        # MySQL 연결
        connection = create_connection()
        cursor = connection.cursor()

        # stocks 데이터 가져오기
        cursor.execute("SELECT stock_idx, stock_name FROM stocks")
        stocks = cursor.fetchall()

        stock_data = []

        for stock in stocks:
            stock_idx = stock[0]
            stock_name = stock[1]

            # 최신 거래량 가져오기
            cursor.execute("""
                SELECT trade_volume
                FROM stock_datas
                WHERE stock_idx = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (stock_idx,))
            trade_volume_row = cursor.fetchone()
            trade_volume = trade_volume_row[0] if trade_volume_row else "데이터 없음"

            # 최신 현재가 가져오기
            cursor.execute("""
                SELECT current_price
                FROM realtime_stocks
                WHERE stock_idx = %s
                ORDER BY create_at DESC
                LIMIT 1
            """, (stock_idx,))
            current_price_row = cursor.fetchone()
            current_price = float(current_price_row[0]) if current_price_row else None

            # 최신 예측값 가져오기
            cursor.execute("""
                SELECT change_summary
                FROM prediction_results
                WHERE stock_idx = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (stock_idx,))
            prediction_row = cursor.fetchone()
            prediction_summary = prediction_row[0] if prediction_row else "데이터 없음"

            stock_data.append({
                "종목코드": stock_idx,
                "종목명": stock_name,
                "현재가": f"{int(current_price):,}원" if current_price is not None else "데이터 없음",
                "거래량": f"{int(trade_volume):,}주" if trade_volume != "데이터 없음" else "데이터 없음",
                "예측(다음날)": prediction_summary
            })

        # JSON 형태로 반환
        return JSONResponse(content={"status": "success", "data": stock_data})

    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        return JSONResponse(content={"status": "error", "message": str(err)})

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@router.get("/stock-data")
async def get_stock_data(id: str = Query(...)):
    """
    주어진 stock_idx(ID)에 해당하는 이름과 현재가를 MySQL에서 가져옵니다.
    """
    connection = None
    try:
        # MySQL 연결
        connection = create_connection()
        cursor = connection.cursor()

        # 이름과 현재가 가져오기
        query = """
        SELECT s.stock_name, rs.current_price
        FROM stocks s
        LEFT JOIN (
            SELECT stock_idx, current_price
            FROM realtime_stocks
            WHERE (stock_idx, create_at) IN (
                SELECT stock_idx, MAX(create_at)
                FROM realtime_stocks
                GROUP BY stock_idx
            )
        ) rs ON s.stock_idx = rs.stock_idx
        WHERE s.stock_idx = %s
        """
        cursor.execute(query, (id,))
        result = cursor.fetchone()

        # 결과 처리
        if result:
            stock_name, current_price = result
            return JSONResponse(content={
                "status": "success",
                "data": {
                    "stock_name": stock_name,
                    "current_price": f"{int(current_price):,}원" if current_price else "데이터 없음"
                }
            })
        else:
            return JSONResponse(content={"status": "error", "message": "Stock ID not found."})

    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        return JSONResponse(content={"status": "error", "message": str(err)})

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_all_stock_data(stock_id: str):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        query = """
        SELECT create_at, current_price
        FROM realtime_stocks
        WHERE stock_idx = %s
        ORDER BY create_at ASC
        """
        cursor.execute(query, (stock_id,))
        rows = cursor.fetchall()
        conn.close()

        # 데이터 정리
        timestamps = [row[0].strftime('%Y-%m-%d %H:%M:%S') for row in rows]
        prices = [float(row[1]) for row in rows]

        return {"timestamps": timestamps, "prices": prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch all stock data: {str(e)}")

# 최신 데이터를 가져오는 함수
def get_latest_stock_data(stock_id: str):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        query = """
        SELECT create_at, current_price
        FROM realtime_stocks
        WHERE stock_idx = %s
        ORDER BY create_at DESC
        LIMIT 1
        """
        cursor.execute(query, (stock_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="No latest stock data found")

        # 데이터 정리
        timestamps = [row[0].strftime('%Y-%m-%d %H:%M:%S')]
        prices = [float(row[1])]

        return {"timestamps": timestamps, "prices": prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest stock data: {str(e)}")

# 모든 데이터 반환 엔드포인트
@router.get("/api/stocks/{stock_id}/all")
async def get_all_stocks(stock_id: str):
    data = get_all_stock_data(stock_id)
    if not data["timestamps"]:  # 데이터가 없는 경우
        raise HTTPException(status_code=404, detail="Stock data not found")
    return JSONResponse(content=data)

# 최신 데이터 반환 엔드포인트
@router.get("/api/stocks/{stock_id}/latest")
async def get_latest_stock(stock_id: str):
    data = get_latest_stock_data(stock_id)
    if not data["timestamps"]:  # 데이터가 없는 경우
        raise HTTPException(status_code=404, detail="Stock data not found")
    return JSONResponse(content=data)