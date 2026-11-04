from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from ..services.websocket_manager import ws_manager
from ..core.security import decode_token

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/auctions")
async def websocket_global(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    await ws_manager.connect_global(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_global(websocket)
    except Exception:
        ws_manager.disconnect_global(websocket)


@router.websocket("/ws/auctions/{rfq_id}")
async def websocket_auction_room(
    websocket: WebSocket,
    rfq_id: int,
    token: Optional[str] = Query(None)
):
    await ws_manager.connect_auction(rfq_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_auction(rfq_id, websocket)
    except Exception:
        ws_manager.disconnect_auction(rfq_id, websocket)
