from fastapi import FastAPI
from controllers import controller

app = FastAPI()

# user_controller의 라우터 등록
app.include_router(controller.router)
