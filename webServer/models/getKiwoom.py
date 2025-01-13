import requests
import threading
import time

FASTAPI_SERVER = "http://localhost:8001"

class DataFetcher:
    def __init__(self, fastapi_server: str):
        """
        DataFetcher 초기화
        """
        self.fastapi_server = fastapi_server
        self.data = []
        self.is_running = False  # 실행 상태 플래그
        self.lock = threading.Lock()  # 데이터 접근 동기화

    def fetch_data(self):
        """
        FastAPI 서버에서 1초 간격으로 데이터를 가져옴
        """
        while self.is_running:
            try:
                response = requests.get(f"{self.fastapi_server}/get-data")
                response.raise_for_status()
                data = response.json().get("data", [])
                if data:
                    with self.lock:
                        self.data = data  # 최신 데이터로 갱신
                else:
                    print("No data available from API.")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data from API: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
            time.sleep(1)

    def start(self):
        """
        데이터를 가져오는 스레드를 시작
        """
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self.fetch_data, daemon=True).start()
            print("DataFetcher started.")

    def stop(self):
        """
        데이터를 가져오는 스레드를 중지
        """
        if self.is_running:
            self.is_running = False
            print("DataFetcher stopped.")

    def get_latest_data(self):
        """
        가장 최근의 데이터를 반환
        """
        with self.lock:  # 동기화를 통해 데이터 무결성 유지
            return self.data
