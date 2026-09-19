import os
import json
from PIL import Image

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(APP_DIR, "image")
ITEMS_JSON = os.path.join(APP_DIR, "items_data.json")

# Целевой размер для качественного отображения 36x36
TARGET_SIZE = (72, 72)

if not os.path.exists(IMAGE_DIR):
    print("[ERROR] Папка image не найдена!")
    exit(1)

# Читаем список предметов, которые реально используются в базе
used_icons = set()
if os.path.exists(ITEMS_JSON):
    with open(ITEMS_JSON, "r", encoding="utf-8") as f:
        items = json.load(f)
        for it in items:
            icon_name = it.get("icon")
            if icon_name:
                used_icons.add(icon_name.lower())

print(f"[*] Активных предметов с иконками: {len(used_icons)}")
print("[*] Начинаем сжатие и подгонку иконок...")

processed_count = 0
freed_bytes = 0
deleted_count = 0

for file in os.listdir(IMAGE_DIR):
    if not file.lower().endswith(".png"):
        continue

    file_path = os.path.join(IMAGE_DIR, file)

    # Удаляем иконку, если её нет в items_data.json (мусор от непередаваемых предметов)
    if used_icons and file.lower() not in used_icons:
        try:
            freed_bytes += os.path.getsize(file_path)
            os.remove(file_path)
            deleted_count += 1
            continue
        except Exception:
            pass

    # Оптимизируем нужные иконки
    try:
        old_size = os.path.getsize(file_path)
        with Image.open(file_path) as img:
            # Конвертируем в RGBA (для сохранения прозрачности фона)
            img = img.convert("RGBA")
            
            # Масштабируем до 72x72 с наилучшей фильтрацией сглаживания
            img.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)
            
            # Перезаписываем с максимальной оптимизацией PNG
            img.save(file_path, format="PNG", optimize=True)

        new_size = os.path.getsize(file_path)
        freed_bytes += max(0, old_size - new_size)
        processed_count += 1

    except Exception as e:
        continue

mb_freed = freed_bytes / (1024 * 1024)

print("=" * 45)
print(f"[OK] Успешно сжато картинок: {processed_count}")
print(f"[OK] Удалено неиспользуемых файлов: {deleted_count}")
print(f"[OK] Освобождено места на диске: ~{mb_freed:.2f} МБ")
print("=" * 45)