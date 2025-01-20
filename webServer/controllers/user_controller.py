from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
from models.getKiwoom import HttpClientModel
from typing import List
from pydantic import BaseModel
import requests
import time
import hashlib

# 유저 테이블 관련 기능 컨트롤러
router = APIRouter()

# 템플릿 경로 설정
templates = Jinja2Templates(directory="views")

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
#             query = "SELECT email, password, username, tel FROM users WHERE email = %s AND password = SHA2(%s, 256)"
#             cursor.execute(query, (email, password))
#             user = cursor.fetchone()

#             if not user:
#                 raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

#             # 세션에 로그인 정보 저장
#             request.session["is_logged_in"] = True
#             request.session["user"] = {"email": user["email"],"password": user["password"], "name": user["username"], "tel": user["tel"]}

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

class UpdateUserInfo(BaseModel):
    email: str
    password: str
    tel: str

@router.post("/api/update-user-info")
async def update_user_info(user_info: UpdateUserInfo, request: Request):
    """
    회원정보 수정 API:
    - 비밀번호와 전화번호를 업데이트.
    - 비밀번호 또는 전화번호 중 하나라도 기존 값과 동일하면 업데이트 중단.
    - 업데이트 후, 이메일로 정보를 다시 조회하여 세션에 저장.
    """
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="데이터베이스 연결 실패")

    try:
        with connection.cursor(dictionary=True) as cursor:
            # 입력된 비밀번호를 SHA256으로 암호화
            hashed_password = hashlib.sha256(user_info.password.encode('utf-8')).hexdigest()

            # 기존 데이터 가져오기
            query = "SELECT password, tel FROM users WHERE email = %s"
            cursor.execute(query, (user_info.email,))
            existing_user = cursor.fetchone()

            if not existing_user:
                return {"success": False, "message": "사용자를 찾을 수 없습니다."}

            # 기존 비밀번호와 전화번호 비교
            if existing_user["password"] == hashed_password:
                return {"success": False, "message": "입력된 비밀번호가 기존 비밀번호와 동일합니다."}

            if existing_user["tel"] == user_info.tel:
                return {"success": False, "message": "입력된 전화번호가 기존 전화번호와 동일합니다."}

            # 데이터 업데이트 (암호화된 비밀번호 저장)
            update_query = """
                UPDATE users
                SET password = %s, tel = %s
                WHERE email = %s
            """
            cursor.execute(update_query, (hashed_password, user_info.tel, user_info.email))
            connection.commit()

            if cursor.rowcount > 0:
                # 업데이트 성공 후, 이메일로 사용자 정보 다시 조회
                cursor.execute("SELECT email, username, tel FROM users WHERE email = %s", (user_info.email,))
                updated_user = cursor.fetchone()

                if updated_user:
                    # 세션에 사용자 정보 저장
                    request.session["user"] = {
                        "email": updated_user["email"],
                        "name": updated_user["username"],
                        "tel": updated_user["tel"]
                    }
                    return {"success": True, "message": "회원정보가 성공적으로 수정되었습니다."}
                else:
                    return {"success": False, "message": "업데이트 후 사용자 정보를 가져오지 못했습니다."}

            return {"success": False, "message": "회원정보 수정에 실패했습니다."}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")
    finally:
        close_connection(connection)

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