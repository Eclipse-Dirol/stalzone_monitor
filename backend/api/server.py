import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from api.stalzone_api import SCAPI
import json
from pathlib import Path

app = FastAPI(title="Stalzone Monitor API")
api = SCAPI() 

class FrontendData(BaseModel):
    item_id: str

class ClientData(BaseModel):
    client_id: str
    client_secret: str

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

@app.post("/api/start")
async def recive_request(client_data: ClientData):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    config_data["client"]["CLIENT_ID"] = client_data.client_id
    config_data["client"]["CLIENT_SECRET"] = client_data.client_secret
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)

    success = await api.start_desktop()

    if not success:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid client data", "error_description": "Не удалось получить токен. Проверьте ключи."}
        )

    return {"status": "success"}

@app.post("/api/view_item")
async def search_auction(payload: FrontendData):
    lots = await api.request_for_auc(item_id=payload.item_id)

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

            lots = await api.constant_loading(item_id)

            if lots:
                safe_lots = jsonable_encoder(lots)
                await websocket.send_json({"status": "update", "data": safe_lots})
            else:
                await websocket.send_json({"status": "error", "message": "Нет лотов"})

            elapsed = asyncio.get_running_loop().time() - t0
            sleep_time = max(0.5 - elapsed, 0)
            await asyncio.sleep(sleep_time)

    except WebSocketDisconnect:
        print(f"Клиент отключился от отслеживания {item_id}")