import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from api.stalzone_api import SCAPI  # Ваш измененный класс

app = FastAPI(title="Stalzone Monitor API")
api = SCAPI() 

class FrontendData(BaseModel):
    item_id: str

@app.post("/api/auction/search")
async def search_auction(item: FrontendData):
    lots = await api.auction(item_id=item.item_id)

    if not lots:
        raise HTTPException(status_code=404, detail="Лоты не найдены")

    return {"status": "success", "data": lots}

@app.websocket("/ws/auction")
async def auction_stream(websocket: WebSocket):
    await websocket.accept()

    try:
        config_data = await websocket.receive_json()
        item_id = config_data["item_id"]

        while True:
            t0 = asyncio.get_running_loop().time()

            lots = await api.auction(item_id=item_id)

            if lots:
                await websocket.send_json({"status": "update", "data": lots})
            else:
                await websocket.send_json({"status": "error", "message": "Нет лотов"})

            elapsed = asyncio.get_running_loop().time() - t0
            sleep_time = max(0.5 - elapsed, 0)
            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        print(f"Клиент отключился от отслеживания {item_id}")