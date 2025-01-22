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
from models.prediction_model import PredictionModel
from models.mySql import create_connection, close_connection
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# FastAPI 애플리케이션 생성
app = FastAPI()

# 정적 파일 경로 설정 (CSS, JS, 이미지 파일)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 경로 설정 (HTML 파일)
templates = Jinja2Templates(directory="views")

# 세션 미들웨어 추가
app.add_middleware(SessionMiddleware, secret_key="123")

# 컨트롤러 라우터 추가
app.include_router(controller_router)
app.include_router(user_controller_router)
app.include_router(stock_controller_router)
app.include_router(trading_controller_router)
app.include_router(fav_controller_router)
app.include_router(kiwoom_controller_router)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 데이터베이스 연결 및 PredictionModel 초기화
db_config = create_connection()
prediction_model = PredictionModel(db_config)

# 비동기 예측 실행
async def run_daily_prediction():
    """
    모든 종목에 대해 병렬로 예측 실행.
    """
    logger.info("[INFO] Running daily prediction...")
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_running_loop()
            tasks = [
                loop.run_in_executor(executor, prediction_model.train_and_predict, stock_idx)
                for stock_idx in prediction_model.stock_list
            ]
            await asyncio.gather(*tasks)
        logger.info("[INFO] Daily prediction completed.")
    except Exception as e:
        logger.error(f"[ERROR] Failed to run daily prediction: {e}")

# 스케줄러 실행 함수
def scheduler_task():
    """
    매일 정해진 시간에 스케줄러를 실행.
    """
    import schedule
    import time

    logger.info("[INFO] Scheduler task started and waiting for the scheduled time...")
    schedule.every().day.at("17:15").do(lambda: asyncio.run(run_daily_prediction()))

    while True:
        schedule.run_pending()
        time.sleep(1)

@app.on_event("startup")
def start_scheduler():
    """
    FastAPI 시작 시 스케줄러 실행.
    """
    thread = threading.Thread(target=scheduler_task, daemon=True)
    thread.start()

@app.on_event("shutdown")
def close_db_connection():
    """
    FastAPI 종료 시 데이터베이스 연결 닫기.
    """
    close_connection(db_config)
    logger.info("[INFO] Database connection closed.")
