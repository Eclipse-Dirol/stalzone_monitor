import os
import json
from datetime import datetime, timezone
import customtkinter as ctk
from PIL import Image

from core.utils import get_app_dir
from core.config_manager import get_deleted_items, add_deleted_item

CATEGORY_MAPPING = {
    "Все": "Все",
    "★ Избранное": "★ Избранное",
    "Оружие": ["оружие", "weapon"],
    "Броня": ["броня", "костюмы", "armor"],
    "Артефакты": ["артефакты", "артефакт", "artefact", "artefacts"],
    "Обвесы": ["обвесы", "прицелы", "надульники", "цевья", "attachment", "attachments"],
    "Разное": ["разное", "прочее", "other", "misc"]
}

class AuctionView(ctk.CTkFrame):
    def __init__(self, master, ws_manager=None):
        super().__init__(master, fg_color="#121417")
        self.ws_manager = ws_manager
        self.db_path = os.path.join(get_app_dir(), "items_data.json")
        self.images_dir = os.path.join(get_app_dir(), "image")

        self.current_category = "Все"
        self.current_search = ""
        self.current_selected_item = None
        self.image_cache = {}

        self.items = self._load_database()

        self._build_ui()
        self._filter_and_display_items()

    def _load_database(self):
        """Загрузка базы данных с фильтрацией удалённых предметов и боеприпасов"""
        items = []
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
            except Exception as e:
                print(f"[ERROR] Ошибка чтения items_data.json: {e}")

        deleted_set = set(get_deleted_items())
        ammo_keywords = ("боеприпас", "патрон", "снаряд", "ammo", "ammunition")

        active_items = []
        for it in items:
            item_id = str(it.get("id"))
            if item_id in deleted_set:
                continue

            cat_lower = str(it.get("category", "")).lower()
            if any(kw in cat_lower for kw in ammo_keywords):
                continue

            active_items.append(it)

        return active_items

    def _build_ui(self):
        # Верхняя панель управления (поиск и категории)
        self.top_frame = ctk.CTkFrame(self, height=50, fg_color="#181a1f", corner_radius=0)
        self.top_frame.pack(fill="x", side="top")

        # Поле поиска
        self.search_entry = ctk.CTkEntry(
            self.top_frame,
            placeholder_text="Поиск по названию...",
            width=240,
            height=34,
            corner_radius=6
        )
        self.search_entry.pack(side="left", padx=(15, 10), pady=8)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Категории (без боеприпасов)
        categories = ["Все", "★ Избранное", "Оружие", "Броня", "Артефакты", "Обвесы", "Разное"]
        self.cat_buttons = []

        for cat in categories:
            btn = ctk.CTkButton(
                self.top_frame,
                text=cat,
                width=80,
                height=32,
                corner_radius=6,
                fg_color="#232730" if cat != "Все" else "#278191",
                hover_color="#1e6572",
                command=lambda c=cat: self._set_category(c)
            )
            btn.pack(side="left", padx=3, pady=8)
            self.cat_buttons.append(btn)

        # Основной контейнер с разделением на каталог и лоты
        self.content_panes = ctk.CTkFrame(self, fg_color="transparent")
        self.content_panes.pack(fill="both", expand=True, padx=15, pady=10)

        # Левая колонка: каталог предметов
        self.left_pane = ctk.CTkFrame(self.content_panes, fg_color="#16181d", corner_radius=8)
        self.left_pane.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.items_scroll = ctk.CTkScrollableFrame(self.left_pane, fg_color="transparent")
        self.items_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Правая колонка: текущие лоты выбранного предмета
        self.right_pane = ctk.CTkFrame(self.content_panes, width=460, fg_color="#16181d", corner_radius=8)
        self.right_pane.pack(side="right", fill="both", padx=(8, 0))
        self.right_pane.pack_propagate(False)

        # Заголовок лотов
        self.lot_header = ctk.CTkFrame(self.right_pane, height=45, fg_color="transparent")
        self.lot_header.pack(fill="x", padx=12, pady=(10, 5))

        self.selected_item_lbl = ctk.CTkLabel(
            self.lot_header,
            text="Выберите предмет",
            font=("Segoe UI", 15, "bold"),
            anchor="w"
        )
        self.selected_item_lbl.pack(side="left", fill="x", expand=True)

        self.lots_status_lbl = ctk.CTkLabel(
            self.lot_header,
            text="",
            font=("Segoe UI", 11),
            text_color="#888888"
        )
        self.lots_status_lbl.pack(side="right")

        # Контейнер для карточек лотов
        self.lots_scroll_frame = ctk.CTkScrollableFrame(self.right_pane, fg_color="transparent")
        self.lots_scroll_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    def _set_category(self, cat_name: str):
        self.current_category = cat_name
        for btn in self.cat_buttons:
            if btn.cget("text") == cat_name:
                btn.configure(fg_color="#278191")
            else:
                btn.configure(fg_color="#232730")
        self._filter_and_display_items()

    def _on_search_changed(self, event=None):
        self.current_search = self.search_entry.get().strip().lower()
        self._filter_and_display_items()

    def _filter_and_display_items(self):
        for w in self.items_scroll.winfo_children():
            w.destroy()

        mapping = CATEGORY_MAPPING.get(self.current_category, "Все")

        for it in self.items:
            name = str(it.get("name", ""))
            category = str(it.get("category", "")).lower()

            if self.current_search and self.current_search not in name.lower():
                continue

            if self.current_category != "Все":
                if isinstance(mapping, list):
                    if not any(sub in category for sub in mapping):
                        continue
                elif self.current_category == "★ Избранное":
                    if not it.get("is_favorite", False):
                        continue

            self._render_item_card(it)

    def _render_item_card(self, it: dict):
        card = ctk.CTkFrame(self.items_scroll, height=52, fg_color="#20242c", corner_radius=6)
        card.pack(fill="x", pady=3, padx=2)

        # Загрузка иконки
        icon_name = it.get("icon")
        img_ctk = None
        if icon_name:
            if icon_name in self.image_cache:
                img_ctk = self.image_cache[icon_name]
            else:
                img_path = os.path.join(self.images_dir, icon_name)
                if os.path.exists(img_path):
                    try:
                        pil_img = Image.open(img_path)
                        img_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(32, 32))
                        self.image_cache[icon_name] = img_ctk
                    except Exception:
                        pass

        if img_ctk:
            img_lbl = ctk.CTkLabel(card, text="", image=img_ctk)
            img_lbl.pack(side="left", padx=8)

        # Название предмета
        name_lbl = ctk.CTkLabel(
            card,
            text=it.get("name", "Без названия"),
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        name_lbl.pack(side="left", fill="x", expand=True, padx=5)

        # Кнопка просмотра лотов
        view_btn = ctk.CTkButton(
            card,
            text="Лоты",
            width=65,
            height=28,
            font=("Segoe UI", 11, "bold"),
            fg_color="#278191",
            hover_color="#1e6572",
            command=lambda item=it: self.on_select_item(item)
        )
        view_btn.pack(side="right", padx=6)

        # Кнопка удаления (крестик)
        del_btn = ctk.CTkButton(
            card,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            text_color="#888888",
            hover_color="#3a1c1c",
            command=lambda item=it, c_widget=card: self._delete_item(item, c_widget)
        )
        del_btn.pack(side="right", padx=(0, 4))

    def _delete_item(self, item: dict, card_widget):
        item_id = str(item.get("id"))
        add_deleted_item(item_id)
        self.items = [i for i in self.items if str(i.get("id")) != item_id]
        card_widget.destroy()

    def on_select_item(self, item: dict):
        """Отправка подписки на получение лотов в WebSocket"""
        self.current_selected_item = item
        item_id = item.get("id")

        self.selected_item_lbl.configure(text=item.get("name", "Предмет"))
        self._clear_lots_container()
        self._set_lots_status("Загрузка актуальных лотов...", color="#3498db")

        if self.ws_manager and item_id:
            # Отправка события бэкенду
            self.ws_manager.send_event("subscribe_item", {"item_id": item_id})

    def update_real_lots(self, payload: dict):
        """Обработка данных, поступивших от бэкенда через WebSocket"""
        lots = payload.get("data", [])
        self._clear_lots_container()

        if not lots:
            self._set_lots_status("Активных лотов нет", color="#e67e22")
            return

        current_id = self.current_selected_item.get("id") if self.current_selected_item else None
        first_lot_id = lots[0].get("itemId")
        if current_id and first_lot_id and current_id != first_lot_id:
            return

        self._set_lots_status(f"Найдено лотов: {len(lots)}", color="#2ecc71")

        # Сортировка по цене выкупа
        sorted_lots = sorted(
            lots,
            key=lambda x: (x.get("buyoutPrice") or float("inf"), x.get("startPrice") or 0)
        )

        for lot in sorted_lots:
            self._render_single_lot_card(lot)

    def _render_single_lot_card(self, lot: dict):
        row = ctk.CTkFrame(self.lots_scroll_frame, height=48, corner_radius=6, fg_color="#20242c")
        row.pack(fill="x", pady=3, padx=4)

        amount = lot.get("amount", 1)
        amt_text = f"x{amount}" if amount > 1 else "1 шт."
        ctk.CTkLabel(
            row,
            text=amt_text,
            width=50,
            font=("Segoe UI", 12, "bold"),
            text_color="#3498db"
        ).pack(side="left", padx=(10, 5))

        buyout = lot.get("buyoutPrice")
        start = lot.get("startPrice")
        cur_price = lot.get("currentPrice")

        price_parts = []
        if buyout and buyout > 0:
            price_parts.append(f"Выкуп: {buyout:,} ₽".replace(",", " "))
        if cur_price and cur_price > 0:
            price_parts.append(f"Ставка: {cur_price:,} ₽".replace(",", " "))
        elif start and start > 0:
            price_parts.append(f"Старт: {start:,} ₽".replace(",", " "))

        price_str = "   |   ".join(price_parts) if price_parts else "Цена не указана"

        ctk.CTkLabel(
            row,
            text=price_str,
            font=("Segoe UI", 13, "bold"),
            text_color="#ffffff",
            anchor="w"
        ).pack(side="left", fill="x", expand=True, padx=10)

        end_time_str = lot.get("endTime")
        time_left_str = self._calculate_time_left(end_time_str)

        ctk.CTkLabel(
            row,
            text=f"⏱ {time_left_str}",
            font=("Segoe UI", 11),
            text_color="#95a5a6"
        ).pack(side="right", padx=12)

    @staticmethod
    def _calculate_time_left(end_time_str: str) -> str:
        if not end_time_str:
            return "—"
        try:
            clean_str = end_time_str.replace("Z", "+00:00")
            end_dt = datetime.fromisoformat(clean_str)
            now_dt = datetime.now(timezone.utc)

            delta = end_dt - now_dt
            total_seconds = int(delta.total_seconds())

            if total_seconds <= 0:
                return "Завершен"

            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60

            if days > 0:
                return f"{days} д {hours} ч"
            if hours > 0:
                return f"{hours} ч {minutes} мин"
            return f"{minutes} мин"
        except Exception:
            return end_time_str[:10]

    def _clear_lots_container(self):
        for child in self.lots_scroll_frame.winfo_children():
            child.destroy()

    def _set_lots_status(self, text: str, color: str = "#888888"):
        self.lots_status_lbl.configure(text=text, text_color=color)