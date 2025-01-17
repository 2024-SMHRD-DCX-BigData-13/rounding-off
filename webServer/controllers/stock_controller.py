from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
from models.getKiwoom import HttpClientModel
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
