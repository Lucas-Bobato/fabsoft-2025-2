from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Dicionário para guardar conexões ativas por jogo_id
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, jogo_id: int):
        await websocket.accept()
        if jogo_id not in self.active_connections:
            self.active_connections[jogo_id] = []
        self.active_connections[jogo_id].append(websocket)

    def disconnect(self, websocket: WebSocket, jogo_id: int):
        if jogo_id in self.active_connections:
            self.active_connections[jogo_id].remove(websocket)

    async def broadcast(self, message: dict, jogo_id: int):
        if jogo_id in self.active_connections:
            for connection in self.active_connections[jogo_id]:
                await connection.send_json(message)

# Cria uma instância única do gestor para ser usada na aplicação
manager = ConnectionManager()