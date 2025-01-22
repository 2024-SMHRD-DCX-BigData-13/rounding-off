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
import schedule
import threading
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

db_config = create_connection()

prediction_model = PredictionModel(db_config)

# 스케줄러 작업 정의
def run_daily_prediction():
    print("[INFO] Running daily prediction...")
    stock_list = [
        "005930", "000660", "035420", "005380", "035720",
        "051910", "005490", "207940", "096770", "068270",
        "006400", "012330", "000270", "066570", "323410",
        "034020", "009830", "015760", "011200", "000120"
    ]
    for stock in stock_list:
        print(f"[INFO] Processing stock: {stock}")
        prediction_model.train_and_predict(stock)

# 스케줄러 실행 함수
def scheduler_task():
    print("[INFO] Scheduler task started and waiting for the scheduled time...")
    schedule.every().day.at("17:15").do(run_daily_prediction)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.on_event("startup")
def start_scheduler():
    thread = threading.Thread(target=scheduler_task, daemon=True)
    thread.start()

@app.on_event("shutdown")
def close_db_connection():
    close_connection(db_config)