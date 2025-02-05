from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
from typing import List
from pydantic import BaseModel
import requests
import time

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

# 로그인 페이지 엔드포인트
@router.get("/stockinfo", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    로그인 페이지 렌더링.
    """
    return templates.TemplateResponse("stockinfo.html", {"request": request})

# 회원가입 페이지 엔드포인트
@router.get("/join", response_class=HTMLResponse)
async def join_page(request: Request):
    """
    회원가입 페이지 렌더링.
    """
    return templates.TemplateResponse("join.html", {"request": request})

# 마이페이지 페이지 엔드포인트
@router.get("/mypage", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    마이페이지 페이지 렌더링.
    """
    return templates.TemplateResponse("mypage.html", {"request": request})

@router.get("/rule")
async def main_page(request: Request):
    """
    약관 페이지 렌더링.
    """
    return templates.TemplateResponse("rule.html", {"request": request})
