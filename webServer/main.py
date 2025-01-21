from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from controllers.controller import router as controller_router
from controllers.user_controller import router as user_controller_router
from controllers.stock_controller import router as stock_controller_router
from controllers.trading_controller import router as trading_controller_router
from controllers.fav_controller import router as fav_controller_router
from controllers.kiwoom_controller import router as kiwoom_controller_router
import subprocess
# FastAPI 애플리케이션 생성
app = FastAPI()

# 정적 파일 경로 설정 (CSS, JS, 이미지 파일)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 경로 설정 (HTML 파일)
templates = Jinja2Templates(directory="views")

app.add_middleware(SessionMiddleware, secret_key="123")

# 컨트롤러 라우터 추가
app.include_router(controller_router)
app.include_router(user_controller_router)
app.include_router(stock_controller_router)
app.include_router(trading_controller_router)
app.include_router(fav_controller_router)
app.include_router(kiwoom_controller_router)


def start_external_file():
    """
    외부 Python 파일 실행
    """
    try:
        # 서브 파일 실행 (비동기로 실행)
        subprocess.Popen(["python", "../kiwoom/kiwoom.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[INFO] External file started successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to start external file: {e}")



@app.on_event("startup")
async def startup_event():
    """
    FastAPI 서버 시작 시 호출되는 이벤트
    """
    print("[INFO] FastAPI is starting...")
    start_external_file()

@app.on_event("shutdown")
async def shutdown_event():
    """
    FastAPI 서버 종료 시 호출되는 이벤트
    """
    print("[INFO] FastAPI is shutting down...")
    # 필요시 외부 프로세스 종료 코드 추가 가능