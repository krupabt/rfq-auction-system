from typing import Dict, List, Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Global listeners (e.g. auction listing page)
        self.global_connections: List[WebSocket] = []
        # Specific RFQ listeners: rfq_id -> List[WebSocket]
        self.rfq_rooms: Dict[int, List[WebSocket]] = {}

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        self.global_connections.append(websocket)

    def disconnect_global(self, websocket: WebSocket):
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)

    async def connect_rfq(self, rfq_id: int, websocket: WebSocket):
        await websocket.accept()
        if rfq_id not in self.rfq_rooms:
            self.rfq_rooms[rfq_id] = []
        self.rfq_rooms[rfq_id].append(websocket)

    def disconnect_rfq(self, rfq_id: int, websocket: WebSocket):
        if rfq_id in self.rfq_rooms and websocket in self.rfq_rooms[rfq_id]:
            self.rfq_rooms[rfq_id].remove(websocket)
            if not self.rfq_rooms[rfq_id]:
                del self.rfq_rooms[rfq_id]

    async def broadcast_rfq(self, rfq_id: int, message: Dict[str, Any]):
        """Broadcasts a message to all users viewing a specific RFQ."""
        if rfq_id in self.rfq_rooms:
            disconnected = []
            for connection in self.rfq_rooms[rfq_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            for dead in disconnected:
                self.disconnect_rfq(rfq_id, dead)

    async def broadcast_global(self, message: Dict[str, Any]):
        """Broadcasts to all connected global clients."""
        disconnected = []
        for connection in self.global_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for dead in disconnected:
            self.disconnect_global(dead)


ws_manager = ConnectionManager()
