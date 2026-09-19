import os
import json
import shutil

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "stalcraft-database"))
RU_ITEMS_DIR = os.path.join(DB_DIR, "ru", "items")
TARGET_IMAGE_DIR = os.path.join(APP_DIR, "image")
BLACKLIST_FILE = os.path.join(APP_DIR, "blacklist.json")
OUTPUT_FILE = os.path.join(APP_DIR, "items_data.json")

os.makedirs(TARGET_IMAGE_DIR, exist_ok=True)

if not os.path.exists(DB_DIR):
    print(f"[ERROR] Папка {DB_DIR} не найдена!")
    exit(1)

CATEGORY_MAP = {
    "weapon": "Оружие",
    "armor": "Броня",
    "artefact": "Артефакты",
    "attachment": "Обвесы",
    "bullet": "Боеприпасы",
    "grenade": "Гранаты",
    "medicine": "Медицина",
    "device": "Устройства",
    "container": "Контейнеры",
    "misc": "Разное"
}

# Загрузка пользовательского черного списка
blacklist = set()
if os.path.exists(BLACKLIST_FILE):
    try:
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            raw_bl = json.load(f)
            blacklist = {str(x).strip().lower() for x in raw_bl}
            print(f"[*] Загружен черный список пользователя: {len(blacklist)} позиций.")
    except Exception as e:
        print(f"[!] Не удалось прочитать blacklist.json: {e}")

print("[*] Сканирование картинок в репозитории...")
png_index = {}
for root, _, files in os.walk(DB_DIR):
    for f in files:
        if f.lower().endswith(".png"):
            png_index[f.lower()] = os.path.join(root, f)
            png_index[os.path.splitext(f)[0].lower()] = os.path.join(root, f)

print("[*] Сбор базы предметов...")
raw_items = []
skipped_by_user = 0

for root, _, files in os.walk(RU_ITEMS_DIR):
    rel_subfolder = os.path.relpath(root, RU_ITEMS_DIR).split(os.sep)[0].lower()
    cat_label = CATEGORY_MAP.get(rel_subfolder, "Разное")

    for file in files:
        if not file.endswith(".json"):
            continue

        file_path = os.path.join(root, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            item_id = str(data.get("id", "")).strip()
            name_obj = data.get("name", {})
            name_ru = ""
            if isinstance(name_obj, dict):
                name_ru = name_obj.get("lines", {}).get("ru", "").strip()

            if not item_id or not name_ru:
                continue

            # Отсекаем только явный технический мусор базы
            if name_ru.startswith("[") or "тест" in name_ru.lower():
                continue

            # Проверка по вашему черному списку (по ID или точному имени)
            if item_id.lower() in blacklist or name_ru.lower() in blacklist:
                skipped_by_user += 1
                continue

            # Поиск иконки
            raw_icon = data.get("icon", "")
            icon_basename = os.path.basename(raw_icon).lower() if raw_icon else ""

            src_png = None
            if icon_basename in png_index:
                src_png = png_index[icon_basename]
            elif f"{item_id.lower()}.png" in png_index:
                src_png = png_index[f"{item_id.lower()}.png"]

            icon_saved_name = ""
            if src_png:
                icon_saved_name = f"{item_id}.png"
                dst_png = os.path.join(TARGET_IMAGE_DIR, icon_saved_name)
                if not os.path.exists(dst_png):
                    try:
                        shutil.copy2(src_png, dst_png)
                    except Exception:
                        pass

            raw_items.append({
                "id": item_id,
                "name": name_ru,
                "category": cat_label,
                "icon": icon_saved_name
            })
        except Exception:
            continue

# Чистая дедупликация (по названию): если имя дублируется, берём версию с иконкой
unique_dict = {}
for it in raw_items:
    n = it["name"]
    if n not in unique_dict:
        unique_dict[n] = it
    else:
        if not unique_dict[n]["icon"] and it["icon"]:
            unique_dict[n] = it

final_items = list(unique_dict.values())
final_items.sort(key=lambda x: x["name"])

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_items, f, ensure_ascii=False, separators=(',', ':'))

print("=" * 50)
print(f"[OK] Собрано уникальных предметов: {len(final_items)}")
if skipped_by_user:
    print(f"[*] Отсеяно вашим черным списком: {skipped_by_user}")
print("=" * 50)