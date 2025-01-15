import requests


class HttpClientModel:
    """
    다른 서버로 POST 요청을 보내는 모델
    """

    def __init__(self, base_url):
        """
        초기화 메서드
        :param base_url: 요청할 서버의 기본 URL
        """
        self.base_url = base_url

    def post_request(self, endpoint: str, payload: dict):
        """
        POST 요청을 보내는 메서드
        :param endpoint: 요청할 API 엔드포인트
        :param payload: 요청 데이터 (JSON 형식)
        :return: 서버의 응답 데이터
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, json=payload)

            # 응답 상태 확인
            if response.status_code == 200:
                return response.json()  # JSON 형식으로 반환
            else:
                raise Exception(f"오류: {response.status_code}, 응답: {response.text}")
        except Exception as e:
            raise Exception(f"POST 요청 실패: {e}")
