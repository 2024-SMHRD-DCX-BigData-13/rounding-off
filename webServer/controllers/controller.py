# from fastapi import APIRouter, Form, HTTPException, Request
# from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
# import bcrypt  # 비밀번호 해시화에 사용
# from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수

# router = APIRouter()

# # 템플릿 경로 설정
# templates = Jinja2Templates(directory="views")

# # 메인 페이지 엔드포인트
# @router.get("/", response_class=RedirectResponse)
# async def read_root():
#     return RedirectResponse(url="/main")

# @router.get("/main")
# async def main_page(request: Request):
#     return templates.TemplateResponse("main.html", {"request": request})

# # 로그인 페이지 엔드포인트
# @router.get("/login", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

# # 회원 가입 페이지 엔드포인트
# @router.get("/join", response_class=HTMLResponse)
# async def join_page(request: Request):
#     return templates.TemplateResponse("join.html", {"request": request})

# @router.post("/login")
# async def login(request: Request, email: str = Form(...), password: str = Form(...)):
#     connection = create_connection()
#     if not connection:
#         raise HTTPException(status_code=500, detail="데이터베이스 연결에 실패했습니다.")

#     try:
#         with connection.cursor(dictionary=True) as cursor:
#             # 이메일로 사용자 정보 가져오기
#             query = "SELECT email, password, username FROM users WHERE email = %s"
#             cursor.execute(query, (email,))
#             user = cursor.fetchone()

#             if not user:
#                 raise HTTPException(status_code=401, detail="이메일이 등록되어 있지 않습니다.")

#             if user['password'] != password:
#                 raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")

#             # 세션에 로그인 정보 저장
#             request.session["is_logged_in"] = True
#             request.session["user"] = {"email": user["email"], "name": user["username"]}

#             return RedirectResponse(url="/", status_code=303)

#     finally:
#         close_connection(connection)

# # 로그인 상태 체크 API
# @router.get("/api/check-login")
# async def check_login(request: Request):
#     user = request.session.get("user")
#     if user:
#         return {"isLoggedIn": True, "user": user}
#     return {"isLoggedIn": False}

# # 로그아웃 처리
# @router.post("/logout")
# async def logout(request: Request):
#     request.session.clear()
#     return {"success": True, "message": "로그아웃 성공"}

# # 회원 가입 처리
# @router.post("/register")
# async def register(request: Request, email: str = Form(...), password: str = Form(...), name: str = Form(...)):
#     # 비밀번호 해시화
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
#     # DB 연결
#     try:
#         connection = create_connection()
#         if connection is None:
#             raise HTTPException(status_code=500, detail="DB 연결 실패")
        
#         cursor = connection.cursor()
        
#         # 이메일 중복 체크
#         cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
#         user = cursor.fetchone()
#         if user:
#             raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
        
#         # 사용자 정보 DB에 저장
#         cursor.execute(
#             "INSERT INTO users (email, password, name) VALUES (%s, %s, %s)",
#             (email, hashed_password, name)
#         )
        
#         connection.commit()  # 변경 사항 저장

#         cursor.close()
#         connection.close()

#         return {"message": "회원 가입 성공"}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"DB 오류: {str(e)}")
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수

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
    return templates.TemplateResponse("main.html", {"request": request})

# 로그인 페이지 엔드포인트
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    로그인 페이지 렌더링.
    """
    return templates.TemplateResponse("login.html", {"request": request})

# 회원가입 페이지 엔드포인트
@router.get("/join", response_class=HTMLResponse)
async def join_page(request: Request):
    """
    회원가입 페이지 렌더링.
    """
    return templates.TemplateResponse("join.html", {"request": request})

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    """
    로그인 처리:
    - 이메일과 비밀번호를 확인하여 세션에 로그인 정보를 저장.
    - 유효하지 않을 경우 에러 메시지 반환.
    """
    connection = create_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="데이터베이스 연결에 실패했습니다.")

    try:
        with connection.cursor(dictionary=True) as cursor:
            # 이메일로 사용자 정보 가져오기
            query = "SELECT email, password, username FROM users WHERE email = %s AND password = SHA2(%s, 256)"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()

            if not user:
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

            # 세션에 로그인 정보 저장
            request.session["is_logged_in"] = True
            request.session["user"] = {"email": user["email"], "name": user["username"]}

            return RedirectResponse(url="/", status_code=303)

    finally:
        close_connection(connection)

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
@router.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), username: str = Form(...)):
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
            "INSERT INTO users (email, password, username) VALUES (%s, SHA2(%s, 256), %s)",
            (email, password, username)
        )

        connection.commit()  # 변경 사항 저장
        cursor.close()
        connection.close()

        return {"message": "회원 가입 성공"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 오류: {str(e)}")

