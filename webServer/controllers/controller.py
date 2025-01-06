from fastapi import APIRouter, Request
from models.model import User
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="views")

# 사용자 로그인 상태 확인
fake_users_db = {
    "user1": {"username": "user1", "email": "user1@example.com", "is_authenticated": True},
    "user2": {"username": "user2", "email": "user2@example.com", "is_authenticated": False}
}

@router.get("/")
async def home(request: Request):
    # 예시로 'user1' 사용자를 로그인 상태로 설정
    user = fake_users_db["user1"]  # 실제로는 세션이나 쿠키에서 사용자 정보를 가져옵니다.
    data = {"title": "FastAPI with MVC", "user": user}
    return templates.TemplateResponse("index.html", {"request": request, "data": data})
