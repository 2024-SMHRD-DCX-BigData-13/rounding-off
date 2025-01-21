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


# 주식 테이블블 관련 기능 컨트롤러
router = APIRouter()

@router.get("/api/receive_data")
async def receive_data(request: Request):
    try:
        data = await request.json()
        print("수신된 데이터:", data)
        return {"status": "success", "message": "데이터가 성공적으로 수신되었습니다.", "received_count": len(data)}
    except Exception as e:
        return {"status": "error", "message": f"오류 발생: {str(e)}"}



# 예측 값을 캐싱하기 위한 딕셔너리
prediction_cache = {}



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

            # 예측(다음날) 생성 (다양한 변동 비율 사용)
            if current_price is not None:
                if stock_idx not in prediction_cache:
                    # 변동 비율: -5% ~ +10% 범위에서 선택
                    change_percentage = random.choice([-5, -3, -1, 1, 3, 5, 7, 10])
                    prediction = current_price + current_price * 0.01 * change_percentage
                    formatted_prediction = f"{int(prediction):,}원 ({change_percentage:+}%)"
                    prediction_cache[stock_idx] = formatted_prediction
                else:
                    formatted_prediction = prediction_cache[stock_idx]
            else:
                formatted_prediction = "데이터 없음"

            stock_data.append({
                "종목코드" : stock_idx,
                "종목명": stock_name,
                "현재가": f"{int(current_price):,}원" if current_price is not None else "데이터 없음",
                "거래량": f"{int(trade_volume):,}주" if trade_volume != "데이터 없음" else "데이터 없음",
                "예측(다음날)": formatted_prediction
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


trade_data = [
    {"날짜" : "2025.01.15", "종목명":"삼성전자","평가손익":"+720,00원(1.1%)","거래대금":"65,160,000원","거래량":"1200주","구분":"매도"},
    {"날짜" : "2025.01.15", "종목명":"LG에너지솔루션","평가손익":"+5,000,000원(0.1%)","거래대금":"3,520,000,000원","거래량":"10000주","구분":"매도"}
]

@router.get("/trade")
async def trade(request: Request):
    """
    거래 내역 데이터 전달
    """
    return JSONResponse(content={"status": "success", "data": trade_data})



mystocks = [
    {"종목명":"삼성전자","현재가":"65,000원","평가손익":"+ 500,000원","매입단가":"60,000원","보유수량":"100주"},
    {"종목명":"LG에너지솔루션","현재가":"390,000원","평가손익":"- 500,000원","매입단가":"400,000원","보유수량":"50주"}
]

@router.get("/mystocks")
async def get_stocks(request: Request):
    """
    보유 종목 데이터 전달
    """
    return JSONResponse(content={"status": "success", "data": mystocks})



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


class FavoriteRequest(BaseModel):
    email: str
    stock_id: str

# 즐겨찾기 추가
@router.post("/fav_insert")
async def add_favorite(fav_request: FavoriteRequest):
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # 중복 확인
        cursor.execute(
            """
            SELECT 1 FROM user_favorites WHERE email = %s AND stock_idx = %s
            """,
            (fav_request.email, fav_request.stock_id),
        )
        if cursor.fetchone():
            return JSONResponse(
                content={"status": "error", "message": "이미 즐겨찾기에 추가된 항목입니다."},
                status_code=400,
            )

        # 즐겨찾기 개수 확인
        cursor.execute(
            """
            SELECT COUNT(*) FROM user_favorites WHERE email = %s
            """,
            (fav_request.email,),
        )
        favorite_count = cursor.fetchone()[0]
        if favorite_count >= 5:
            return JSONResponse(
                content={"status": "error", "message": "즐겨찾기는 최대 5개까지 추가할 수 있습니다."},
                status_code=400,
            )

        # 즐겨찾기 추가
        cursor.execute(
            """
            INSERT INTO user_favorites (email, stock_idx)
            VALUES (%s, %s)
            """,
            (fav_request.email, fav_request.stock_id),
        )
        connection.commit()
        return JSONResponse(
            content={"status": "success", "message": "즐겨찾기 추가 성공"}, status_code=200
        )

    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        return JSONResponse(
            content={"status": "error", "message": f"데이터베이스 오류: {err.msg}"},
            status_code=500,
        )

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@router.post("/fav_delete")
async def remove_favorite(fav_request: FavoriteRequest):
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # 즐겨찾기 삭제
        cursor.execute(
            """
            DELETE FROM user_favorites WHERE email = %s AND stock_idx = %s
            """,
            (fav_request.email, fav_request.stock_id),
        )
        connection.commit()

        if cursor.rowcount == 0:
            return JSONResponse(
                content={"status": "error", "message": "즐겨찾기에 해당 항목이 없습니다."},
                status_code=400,
            )

        return JSONResponse(
            content={"status": "success", "message": "즐겨찾기 삭제 성공"}, status_code=200
        )

    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        return JSONResponse(
            content={"status": "error", "message": f"데이터베이스 오류: {err.msg}"},
            status_code=500,
        )

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


@router.post("/api/check-favorite")
async def check_favorite(request: FavoriteRequest):
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # 즐겨찾기 확인 쿼리
        query = """
        SELECT COUNT(*)
        FROM user_favorites
        WHERE email = %s AND stock_idx = %s
        """
        cursor.execute(query, (request.email, request.stock_id))
        result = cursor.fetchone()

        # 결과 확인
        is_favorite = result[0] > 0

        return {
            "status": "success",
            "isFavorite": is_favorite
        }
    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()



class FavoriteCheck(BaseModel):
    email: str

@router.post("/favorites")
async def get_favorites(fav_request: FavoriteCheck):
    connection = None
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # 관심 종목 및 최신 현재가 가져오기
        query = """
            SELECT 
                s.stock_idx,
                s.stock_name,
                r.current_price
            FROM 
                user_favorites f
            JOIN stocks s
                ON f.stock_idx = s.stock_idx
            JOIN (
                SELECT 
                    stock_idx, 
                    MAX(create_at) AS latest_create_at
                FROM 
                    realtime_stocks
                GROUP BY 
                    stock_idx
            ) latest_r
                ON f.stock_idx = latest_r.stock_idx
            JOIN realtime_stocks r
                ON latest_r.stock_idx = r.stock_idx
                AND latest_r.latest_create_at = r.create_at
            WHERE 
                f.email = %s;
        """
        cursor.execute(query, (fav_request.email,))
        favorites = cursor.fetchall()

        if not favorites:
            print("[DEBUG] No favorites found for email:", fav_request.email)

        # 결과 처리
        favorite_data = []
        for row in favorites:
            stock_idx = row[0]
            stock_name = row[1]
            current_price = float(row[2])  # Decimal을 float로 변환

            # 고정된 예측값 계산 (예: +5%)
            prediction = current_price + current_price * 0.05
            prediction_str = f"{int(prediction):,}원 (+5%)"

            favorite_data.append({
                "stock_idx" : stock_idx,
                "stock_name": stock_name,
                "current_price": int(current_price),
                "prediction": prediction_str,
            })

        return JSONResponse(content={"status": "success", "data": favorite_data})

    except mysql.connector.Error as err:
        print(f"[ERROR] Database error: {err}")
        return JSONResponse(
            content={"status": "error", "message": f"Database error: {err.msg}"},
            status_code=500,
        )

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
