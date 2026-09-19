import os
import json

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ITEMS_FILE = os.path.join(APP_DIR, "items_data.json")
IMAGE_DIR = os.path.join(APP_DIR, "image")

CONFIG_LOCATIONS = [
    os.path.join(APP_DIR, "config.json"),
    os.path.join(APP_DIR, "dist", "config.json")
]

def clean_database_and_images():
    print("[1/3] Поиск удалённых предметов...")
    deleted_ids = set()

    # Считываем удаленные из всех возможных мест (корень или dist/)
    for cfg_path in CONFIG_LOCATIONS:
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    for i_id in cfg.get("deleted_items", []):
                        deleted_ids.add(str(i_id))
            except Exception as e:
                print(f"[!] Ошибка чтения {cfg_path}: {e}")

    print(f"[*] Всего зафиксировано удалённых предметов: {len(deleted_ids)}")

    # Перезаписываем исходный items_data.json
    active_items = []
    active_icons = set()

    if os.path.exists(ITEMS_FILE):
        try:
            with open(ITEMS_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    if str(item.get("id")) not in deleted_ids:
                        active_items.append(item)
                        icon = item.get("icon")
                        if icon:
                            active_icons.add(icon.lower())

            with open(ITEMS_FILE, "w", encoding="utf-8") as f:
                json.dump(active_items, f, ensure_ascii=False, separators=(',', ':'))

            print(f"[OK] В базе сохранено {len(active_items)} активных позиций.")
        except Exception as e:
            print(f"[ERROR] Ошибка записи в items_data.json: {e}")
            return

    # Удаляем картинки с диска
    print("[2/3] Очистка папки image от удалённых предметов...")
    deleted_images_count = 0
    if os.path.exists(IMAGE_DIR):
        for file in os.listdir(IMAGE_DIR):
            if file.lower().endswith(".png"):
                if file.lower() not in active_icons:
                    try:
                        os.remove(os.path.join(IMAGE_DIR, file))
                        deleted_images_count += 1
                    except Exception:
                        pass

    print(f"[OK] Удалено неиспользуемых иконок: {deleted_images_count}")

if __name__ == "__main__":
    clean_database_and_images()