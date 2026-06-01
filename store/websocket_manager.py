import json
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

subscriptions: Set[WebSocket] = set()


async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    subscriptions.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions.discard(websocket)


async def send_data_to_subscribers(data) -> None:
    for websocket in subscriptions:
        await websocket.send_json(json.dumps(data))