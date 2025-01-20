from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import json

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Real-Time Stock Data Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f9;
                color: #333;
            }
            header {
                background-color: #6200ea;
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 1.5em;
            }
            main {
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 80vh;
            }
            .data-container {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                text-align: center;
                max-width: 400px;
                width: 100%;
            }
            .data-container h2 {
                margin: 0;
                color: #6200ea;
            }
            .data-container p {
                font-size: 1.2em;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <header>Real-Time Stock Data</header>
        <main>
            <div class="data-container">
                <h2 id="stock-code">Loading...</h2>
                <p id="current-price">Current Price: -</p>
                <p id="volume">Volume: -</p>
            </div>
        </main>
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);

                document.getElementById('stock-code').textContent = `Stock Code: ${data.stock_code}`;
                document.getElementById('current-price').textContent = `Current Price: ${data.current_price}`;
                document.getElementById('volume').textContent = `Volume: ${data.volume}`;
            };

            ws.onopen = function() {
                console.log("Connected to WebSocket server!");
            };

            ws.onclose = function() {
                console.log("WebSocket connection closed.");
                document.getElementById('stock-code').textContent = "Disconnected";
                document.getElementById('current-price').textContent = "-";
                document.getElementById('volume').textContent = "-";
            };

            ws.onerror = function(error) {
                console.log("WebSocket error:", error);
            };
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    메인 서버 웹소켓 엔드포인트
    """
    await websocket.accept()
    print("[DEBUG] WebSocket client connected.")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[DEBUG] Received from Kiwoom: {data}")
            await websocket.send_text(data)  # 클라이언트로 데이터 전송
    except WebSocketDisconnect:
        print("[DEBUG] WebSocket client disconnected.")
