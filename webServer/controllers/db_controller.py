# controllers/db_controller.py

from fastapi import APIRouter
from models.mySql import create_connection, close_connection

router = APIRouter()

# MySQL 연결 테스트 엔드포인트
@router.get("/test-db")
async def test_db_connection():
    connection = create_connection()
    if connection:
        close_connection(connection)
        return {"status": "MySQL 연결 성공"}
    return {"status": "MySQL 연결 실패"}
