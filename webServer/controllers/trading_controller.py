from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.mySql import create_connection, close_connection  # MySQL 연결을 위한 함수
from models.getKiwoom import HttpClientModel
from typing import List
from pydantic import BaseModel
import requests
import time


# 거래 기록 테이블 관련 기능 컨트롤러
router = APIRouter()