from typing import Dict, List, Any, Optional
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        # Global channels: list of connected sockets
        self.global_connections: List[WebSocket] = []
        # Auction rooms: rfq_id -> list of connected sockets
        self.auction_rooms: Dict[int, List[WebSocket]] = {}

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        self.global_connections.append(websocket)

    def disconnect_global(self, websocket: WebSocket):
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)

    async def connect_auction(self, rfq_id: int, websocket: WebSocket):
        await websocket.accept()
        if rfq_id not in self.auction_rooms:
            self.auction_rooms[rfq_id] = []
        self.auction_rooms[rfq_id].append(websocket)

    def disconnect_auction(self, rfq_id: int, websocket: WebSocket):
        if rfq_id in self.auction_rooms and websocket in self.auction_rooms[rfq_id]:
            self.auction_rooms[rfq_id].remove(websocket)
            if not self.auction_rooms[rfq_id]:
                del self.auction_rooms[rfq_id]

    async def broadcast_to_auction(self, rfq_id: int, event_type: str, data: Any):
        """Broadcasts event to all active watchers of a specific auction room."""
        message = {
            "type": event_type,
            "rfq_id": rfq_id,
            "data": data
        }
        if rfq_id in self.auction_rooms:
            disconnected = []
            for ws in self.auction_rooms[rfq_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(ws)
            for dead in disconnected:
                self.disconnect_auction(rfq_id, dead)

    async def broadcast_global(self, event_type: str, data: Any):
        """Broadcasts global updates (e.g. auction list updates, stats) to all connected clients."""
        message = {
            "type": event_type,
            "data": data
        }
        disconnected = []
        for ws in self.global_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for dead in disconnected:
            self.disconnect_global(dead)


ws_manager = WebSocketManager()
