from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kiwoom_api import KiwoomAPI
from datetime import datetime, timedelta

app = FastAPI()

class StockRequest(BaseModel):
    stock_code: str
    start_date: str  # "YYYYMMDD" 형식


@app.post("/get_stock_data")
def get_stock_data(request: StockRequest):
    """
    키움증권 API를 통해 주식 데이터를 가져오는 엔드포인트
    """
    try:
        # 키움 API 객체 생성
        kiwoom = KiwoomAPI()

        # 로그인
        print("키움증권 로그인 중...")
        kiwoom.login()

        # 데이터 요청
        print(f"종목 코드: {request.stock_code}, 기준일자: {request.start_date}")
        data = kiwoom.get_stock_history(request.stock_code, request.start_date)

        # JSON 응답 생성
        return {"stock_code": request.stock_code, "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
