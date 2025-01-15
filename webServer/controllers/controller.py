from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
from models.getKiwoom import HttpClientModel
from typing import List
from pydantic import BaseModel
import requests
import time

router = APIRouter()

# 템플릿 경로 설정
templates = Jinja2Templates(directory="views")

# 메인 페이지 엔드포인트
@router.get("/", response_class=RedirectResponse)
async def read_root():
    """
    루트 URL 요청 시 /main 페이지로 리다이렉트.
    """
    return RedirectResponse(url="/main")

@router.get("/main")
async def main_page(request: Request):
    """
    메인 페이지 렌더링.
    """
    return templates.TemplateResponse("inin.html", {"request": request})


# 로그인 페이지 엔드포인트
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    로그인 페이지 렌더링.
    """
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 페이지 엔드포인트
@router.get("/stockinfo", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    로그인 페이지 렌더링.
    """
    return templates.TemplateResponse("stockinfo.html", {"request": request})

# 회원가입 페이지 엔드포인트
@router.get("/join", response_class=HTMLResponse)
async def join_page(request: Request):
    """
    회원가입 페이지 렌더링.
    """
    return templates.TemplateResponse("join.html", {"request": request})

# 마이페이지 페이지 엔드포인트
@router.get("/mypage", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    마이페이지 페이지 렌더링.
    """
    return templates.TemplateResponse("mypage.html", {"request": request})

# @router.post("/login")
# async def login(request: Request, email: str = Form(...), password: str = Form(...)):
#     """
#     로그인 처리:
#     - 이메일과 비밀번호를 확인하여 세션에 로그인 정보를 저장.
#     - 유효하지 않을 경우 에러 메시지 반환.
#     """
#     connection = create_connection()
#     if not connection:
#         raise HTTPException(status_code=500, detail="데이터베이스 연결에 실패했습니다.")

#     try:
#         with connection.cursor(dictionary=True) as cursor:
#             # 이메일로 사용자 정보 가져오기
#             query = "SELECT email, password, username FROM users WHERE email = %s AND password = SHA2(%s, 256)"
#             cursor.execute(query, (email, password))
#             user = cursor.fetchone()

#             if not user:
#                 raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

#             # 세션에 로그인 정보 저장
#             request.session["is_logged_in"] = True
#             request.session["user"] = {"email": user["email"], "name": user["username"]}

#             return RedirectResponse(url="/", status_code=303)

#     finally:
#         close_connection(connection)

# 로그인 상태 체크 API
@router.get("/api/check-login")
async def check_login(request: Request):
    """
    로그인 상태 확인:
    - 세션에 저장된 사용자 정보를 반환.
    """
    user = request.session.get("user")
    if user:
        return {"isLoggedIn": True, "user": user}
    return {"isLoggedIn": False}

# 로그아웃 처리
@router.post("/logout")
async def logout(request: Request):
    """
    로그아웃 처리:
    - 세션 정보 초기화.
    """
    request.session.clear()
    return {"success": True, "message": "로그아웃 성공"}

# 회원가입 처리
@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, email: str = Form(...), password: str = Form(...), username: str = Form(...), tel: str = Form(...)):
    """
    회원가입 처리:
    - 이메일 중복 확인 후 사용자를 데이터베이스에 추가.
    - 비밀번호는 MySQL의 SHA2 함수로 암호화하여 저장.
    """
    # DB 연결
    try:
        connection = create_connection()
        if connection is None:
            raise HTTPException(status_code=500, detail="DB 연결 실패")

        cursor = connection.cursor()

        # 이메일 중복 체크
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

        # 사용자 정보 DB에 저장
        cursor.execute(
            "INSERT INTO users (email, password, username, tel) VALUES (%s, SHA2(%s, 256), %s, %s)",
            (email, password, username, tel)
        )

        connection.commit()  # 변경 사항 저장
        cursor.close()
        connection.close()

        return templates.TemplateResponse("main.html", {"request": request})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 오류: {str(e)}")




client = HttpClientModel(base_url="http://127.0.0.1:8001")  # 키움 API 서버 URL

class StockRequest(BaseModel):
    stock_codes: List[str]
    start_date: str

@router.post("/api/fetch_stock_data")
def fetch_stock_data(request: StockRequest):
    results = []
    for stock_code in request.stock_codes:
        try:
            print(f"[메인 서버] 요청 보내기 - 종목코드: {stock_code}, 기준일자: {request.start_date}")
            response = client.post_request(
                endpoint="get_stock_data",
                payload={"stock_code": stock_code, "start_date": request.start_date},
            )
            print(f"[메인 서버] 응답 받음 - 종목코드: {stock_code}, 데이터: {response}")
            results.append({"stock_code": stock_code, "data": response})
        except Exception as e:
            print(f"[메인 서버] 요청 실패 - 종목코드: {stock_code}, 에러: {e}")
            results.append({"stock_code": stock_code, "error": str(e)})
    return {"results": results}


mock_db = {
    "1@1": {
        "password": "1",  # 평문 비밀번호, 실제 환경에서는 해싱 필요
        "username": "TestUser"
    }
}
@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    """
    로그인 처리:
    - 이메일과 비밀번호를 확인하여 세션에 로그인 정보를 저장.
    - 유효하지 않을 경우 에러 메시지 반환.
    """
    # DB 대체 딕셔너리 사용
    user = mock_db.get(email)
    
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

    # 세션에 로그인 정보 저장
    request.session["is_logged_in"] = True
    request.session["user"] = {"email": email, "name": user["username"]}

    return RedirectResponse(url="/", status_code=303)
