import os
import json
import threading
import urllib.request
import urllib.error
from core.utils import get_app_dir

BASE_BACKEND_URL = "http://127.0.0.1:8000/api"
_SESSION_INITIALIZED = False

START_URL = "http://localhost:8000/api/start"

def start_backend_session(client_id: str, client_secret: str) -> tuple[bool, str]:
    """
    Отправляет client_id и client_secret на localhost:8000/api/start.
    Возвращает (True, "OK") при {"status": "success"}
    или (False, "текст ошибки") при ошибке.
    """
    payload = json.dumps({
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip()
    }).encode("utf-8")

    req = urllib.request.Request(
        START_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "StalzoneApp/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            # Проверяем успешный статус
            if data.get("status") == "success":
                return True, "OK"
            
            # Если бэкенд отдал 200 OK, но внутри лежит detail с ошибкой
            if "detail" in data and isinstance(data["detail"], dict):
                err_msg = data["detail"].get("error_description") or data["detail"].get("error")
                return False, err_msg or "Ошибка авторизации"

            return False, "Неизвестный ответ от сервера"

    except urllib.error.HTTPError as e:
        # Перехватываем 400/401/422 ответы от FastAPI
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            detail = err_body.get("detail")
            
            if isinstance(detail, dict):
                err_msg = detail.get("error_description") or detail.get("error")
                return False, err_msg or "Ошибка авторизации"
            
            if isinstance(detail, str):
                return False, detail
        except Exception:
            pass
        return False, f"Ошибка сервера (HTTP {e.code})"

    except urllib.error.URLError:
        return False, "Локальный бэкенд не запущен (localhost:8000)"
    except Exception as e:
        return False, f"Ошибка соединения: {e}"

def _load_credentials():
    """Чтение ключей из локального config.json"""
    cfg_path = os.path.join(get_app_dir(), "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return cfg.get("client_id"), cfg.get("client_secret")
        except Exception:
            pass
    return None, None

def _send_init_request():
    """Разовая отправка ключей бэкенду"""
    global _SESSION_INITIALIZED
    client_id, client_secret = _load_credentials()

    if not client_id or not client_secret:
        return

    payload = json.dumps({
        "client_id": client_id,
        "client_secret": client_secret
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_BACKEND_URL}/init",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "StalzoneApp/1.0"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                _SESSION_INITIALIZED = True
                print("[API] Сессия с бэкендом успешно инициализирована")
    except Exception as e:
        print(f"[API] Локальный бэкенд не запущен или ошибка init: {e}")

def init_backend_session():
    """Запуск разовой авторизации в фоновом потоке при запуске"""
    threading.Thread(target=_send_init_request, daemon=True).start()

def _send_item_request(item_id: str):
    """Максимально быстрый запрос: передается только ID лота"""
    payload = json.dumps({"item_id": item_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_BACKEND_URL}/view_item",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "StalzoneApp/1.0"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            pass
    except Exception:
        # Без лишних принтов в консоль, чтобы не тормозить UI
        pass

def notify_backend_item_viewed(item_id: str):
    """Вызывается при клике на просмотр лота"""
    if not item_id:
        return
    threading.Thread(target=_send_item_request, args=(item_id,), daemon=True).start()

