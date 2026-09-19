import os
import sys
from PIL import Image
import customtkinter as ctk

_IMAGE_CACHE = {}

def resource_path(relative_path: str) -> str:
    """Для статических ассетов (иконки, дефолтная база)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

def get_app_dir() -> str:
    """Возвращает постоянную директорию программы на диске"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_item_icon(icon_name: str, size=(36, 36)):
    """Безопасная загрузка изображения в память без закрытого файлового дескриптора"""
    if not icon_name:
        return None

    cache_key = (icon_name, size)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]
        
    full_path = resource_path(os.path.join("image", icon_name))
    if not os.path.exists(full_path):
        return None
        
    try:
        with Image.open(full_path) as img:
            # Делаем .copy(), чтобы разорвать связь с файлом и не ловить AssertionError
            img_copy = img.convert("RGBA").copy()
            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=size)
            _IMAGE_CACHE[cache_key] = ctk_img
            return ctk_img
    except Exception:
        return None