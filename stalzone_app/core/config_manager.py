import os
import json
from core.utils import get_app_dir

# Всегда сохраняем в постоянную директорию приложения
CONFIG_FILE = os.path.join(get_app_dir(), "config.json")

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(*args, **kwargs):
    cfg = load_config()

    if len(args) == 1 and isinstance(args[0], dict):
        cfg.update(args[0])
    elif len(args) >= 2:
        cfg["client_id"] = args[0]
        cfg["client_secret"] = args[1]
    elif "client_id" in kwargs or "client_secret" in kwargs:
        cfg.update(kwargs)

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить config.json: {e}")

def get_favorites() -> list:
    cfg = load_config()
    favs = cfg.get("favorites", [])
    return favs if isinstance(favs, list) else []

def toggle_favorite(item_id: str) -> bool:
    cfg = load_config()
    favs = cfg.get("favorites", [])
    if not isinstance(favs, list):
        favs = []

    if item_id in favs:
        favs.remove(item_id)
        is_fav = False
    else:
        favs.append(item_id)
        is_fav = True

    cfg["favorites"] = favs
    save_config(cfg)
    return is_fav

def get_deleted_items() -> list:
    cfg = load_config()
    deleted = cfg.get("deleted_items", [])
    return deleted if isinstance(deleted, list) else []

def add_deleted_item(item_id: str):
    cfg = load_config()
    deleted = cfg.get("deleted_items", [])
    if not isinstance(deleted, list):
        deleted = []
    if item_id not in deleted:
        deleted.append(item_id)
        cfg["deleted_items"] = deleted
        save_config(cfg)