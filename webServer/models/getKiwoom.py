import requests

class HttpClientModel:
    def __init__(self, base_url):
        self.base_url = base_url

    def post_request(self, endpoint: str, payload: dict):
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"오류: {response.status_code}, 응답: {response.text}")
        except Exception as e:
            raise Exception(f"POST 요청 실패: {e}")
