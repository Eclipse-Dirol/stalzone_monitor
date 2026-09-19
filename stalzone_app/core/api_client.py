import os
import json
import threading
import urllib.request
import urllib.error
from core.utils import get_app_dir

LOCAL_BACKEND_URL = "http://127.0.0.1:8000/api/view_item"

def _load_local_credentials():
    """Чтение локальной конфигурации из рабочей папки"""
    cfg_path = os.path.join(get_app_dir(), "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("client_id"), cfg.get("client_secret")
        except Exception:
            pass
    return None, None

def _send_request_thread(item_id: str):
    """Отправка параметров на локальный бэкенд"""
    client_id, client_secret = _load_local_credentials()

    payload_data = {
        "item_id": item_id,
        "client_id": client_id,
        "client_secret": client_secret
    }

    payload = json.dumps(payload_data).encode("utf-8")
    
    req = urllib.request.Request(
        LOCAL_BACKEND_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "StalzoneApp/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            # Ответ локального сервиса
            pass
    except urllib.error.URLError as e:
        print(f"[LOCAL BACKEND] Сервис недоступен: {e}")
    except Exception as e:
        print(f"[LOCAL BACKEND] Ошибка запроса: {e}")

def notify_backend_item_viewed(item_id: str):
    """Асинхронный вызов из интерфейса"""
    if not item_id:
        return
    thread = threading.Thread(
        target=_send_request_thread,
        args=(item_id,),
        daemon=True
    )
    thread.start()