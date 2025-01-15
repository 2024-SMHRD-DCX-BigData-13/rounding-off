import httpx

class ExternalAPI:
    KIWOOM_URL = "http://127.0.0.1:8001"  # 요청을 보낼 다른 FastAPI 서버 주소

    @staticmethod
    async def fetch_data_from_other_server(endpoint: str):
        """
        다른 FastAPI 서버로 GET 요청을 보내 데이터를 가져오는 함수.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ExternalAPI.KIWOOM_URL}/{endpoint}")
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()