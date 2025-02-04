from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
from models.getKiwoom import HttpClientModel
from typing import List
from pydantic import BaseModel
import requests
import time



# 관심 종목 테이블 관련 기능 컨트롤러
router = APIRouter()

class FavoriteRequest(BaseModel):
    email: str
    stock_id: str

# 관심종목 추가
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
                content={"status": "error", "message": "이미 관심종목에 추가된 항목입니다."},
                status_code=400,
            )

        # 관심종목 개수 확인
        cursor.execute(
            """
            SELECT COUNT(*) FROM user_favorites WHERE email = %s
            """,
            (fav_request.email,),
        )
        favorite_count = cursor.fetchone()[0]
        if favorite_count >= 5:
            return JSONResponse(
                content={"status": "error", "message": "관심종목는 최대 5개까지 추가할 수 있습니다."},
                status_code=400,
            )

        # 관심종목 추가
        cursor.execute(
            """
            INSERT INTO user_favorites (email, stock_idx)
            VALUES (%s, %s)
            """,
            (fav_request.email, fav_request.stock_id),
        )
        connection.commit()
        return JSONResponse(
            content={"status": "success", "message": "관심종목 추가 성공"}, status_code=200
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

        # 관심종목 삭제
        cursor.execute(
            """
            DELETE FROM user_favorites WHERE email = %s AND stock_idx = %s
            """,
            (fav_request.email, fav_request.stock_id),
        )
        connection.commit()

        if cursor.rowcount == 0:
            return JSONResponse(
                content={"status": "error", "message": "관심종목에 해당 항목이 없습니다."},
                status_code=400,
            )

        return JSONResponse(
            content={"status": "success", "message": "관심종목 삭제 성공"}, status_code=200
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

        # 관심종목 확인 쿼리
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

        # 관심 종목, 최신 현재가 및 예측값 가져오기
        query = """
            SELECT 
                s.stock_idx,
                s.stock_name,
                r.current_price,
                p.change_summary
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
            LEFT JOIN prediction_results p
                ON f.stock_idx = p.stock_idx
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
            prediction = row[3] if row[3] else "N/A"  # 예측값이 없을 경우 "N/A" 처리

            favorite_data.append({
                "stock_idx": stock_idx,
                "stock_name": stock_name,
                "current_price": int(current_price),
                "prediction": prediction,
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
