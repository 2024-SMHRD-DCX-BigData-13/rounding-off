import asyncio
import websockets
import random

# 서버가 클라이언트에게 전송할 메시지를 생성하는 함수
def generate_message():
    return f"Random Data: {random.randint(1, 100)}"

# 웹소켓 서버 핸들러 정의
async def websocket_handler(websocket, path):
    try:
        while True:
            # 클라이언트로 메시지 전송
            message = generate_message()
            await websocket.send(message)
            print(f"Sent: {message}")

            # 메시지 전송 간격 설정
            await asyncio.sleep(1)  # 1초 간격으로 데이터 전송
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")

# 웹소켓 서버 실행
def start_server():
    # 서버 호스트 및 포트 설정
    server = websockets.serve(websocket_handler, "localhost", 8001)

    print("WebSocket server started at ws://localhost:8001")

    # asyncio 이벤트 루프 실행
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    start_server()
