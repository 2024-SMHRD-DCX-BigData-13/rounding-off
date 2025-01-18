from pydantic import BaseModel

# 사용자 모델 정의 (간단한 예시)
class User(BaseModel):
    username: str
    email: str
    is_authenticated: bool = False

