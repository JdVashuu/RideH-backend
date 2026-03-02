from typing import Dict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, trip_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[trip_id] = websocket

    def disconnect(self, trip_id: str):
        self.active_connections.pop(trip_id, None)

    async def send_location(self, trip_id: str, data: dict):
        if trip_id in self.active_connections:
            await self.active_connections[trip_id].send_json(data)


manager = ConnectionManager()
