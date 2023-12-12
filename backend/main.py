from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def handle_client_connection(self, websocket: WebSocket, client_id: int):
        await self.connect(websocket)
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        try:
            while True:
                data = await websocket.receive_text()
                message = {"time": current_time, "clientId": client_id, "message": data}
                await self.broadcast(json.dumps(message))
        except WebSocketDisconnect:
            self.disconnect(websocket)
            message = {"time": current_time, "clientId": client_id, "message": "Offline"}
            await self.broadcast(json.dumps(message))


manager = ConnectionManager()

# define endpoint


@app.get("/")
def Home():
    return "Hola desde WhatsApp"


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.handle_client_connection(websocket, client_id)