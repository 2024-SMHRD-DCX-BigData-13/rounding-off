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
import threading
import schedule
import subprocess
import time
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


def run_prediction_task():
    """
    서버 내에서 실행할 특정 함수 (예측 작업)
    """
    print("[INFO] Running prediction task...")
    try:
        # 여기에 실제 작업 로직을 추가하세요
        print("[INFO] Prediction task executed successfully.")
    except Exception as e:
        print(f"[ERROR] Prediction task failed: {e}")


def run_scheduler():
    """
    스케줄러 실행 루프
    """
    print("[INFO] Scheduler task started...")
    # 매일 지정된 시간에 특정 함수 실행
    schedule.every().day.at("09:15").do(run_prediction_task)

    while True:
        schedule.run_pending()
        time.sleep(1)


@app.on_event("startup")
async def startup_event():
    """
    FastAPI 서버 시작 시 호출되는 이벤트
    """
    print("[INFO] FastAPI is starting...")

    # 스케줄러를 별도의 스레드로 실행
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()


@app.on_event("shutdown")
async def shutdown_event():
    """
    FastAPI 서버 종료 시 호출되는 이벤트
    """
    print("[INFO] FastAPI is shutting down...")