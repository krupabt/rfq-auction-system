from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..websocket_manager import ws_manager

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/rfqs")
async def websocket_global_endpoint(websocket: WebSocket):
    await ws_manager.connect_global(websocket)
    try:
        while True:
            # Keep connection alive; clients may send heartbeats/pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_global(websocket)
    except Exception:
        ws_manager.disconnect_global(websocket)


@router.websocket("/ws/rfqs/{rfq_id}")
async def websocket_rfq_endpoint(websocket: WebSocket, rfq_id: int):
    await ws_manager.connect_rfq(rfq_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_rfq(rfq_id, websocket)
    except Exception:
        ws_manager.disconnect_rfq(rfq_id, websocket)
