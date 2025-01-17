import asyncio
import websockets

async def receive_data():
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            print(f"실시간 데이터: {data}")

asyncio.run(receive_data())
