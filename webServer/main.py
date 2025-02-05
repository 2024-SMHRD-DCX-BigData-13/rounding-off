from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from controllers.controller import router as controller_router
from controllers.user_controller import router as user_controller_router
from controllers.stock_controller import router as stock_controller_router
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
app.include_router(fav_controller_router)
app.include_router(kiwoom_controller_router)

