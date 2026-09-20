import os
import json
import customtkinter as ctk
from PIL import Image

from core.utils import resource_path
from core.config_manager import get_deleted_items, add_deleted_item, get_favorites, toggle_favorite

CATEGORY_MAPPING = {
    "Все": "Все",
    "★ Избранное": "★ Избранное",
    "Оружие": ["оружие", "weapon"],
    "Броня": ["броня", "костюмы", "armor"],
    "Артефакты": ["артефакты", "артефакт", "artefact", "artefacts"],
    "Обвесы": ["обвесы", "прицелы", "надульники", "цевья", "attachment", "attachments"],
    "Разное": ["разное", "прочее", "other", "misc"]
}

ITEMS_PER_PAGE = 30


class AuctionView(ctk.CTkFrame):
    def __init__(self, master, on_open_detail):
        super().__init__(master, fg_color="#121417")
        self.on_open_detail = on_open_detail

        self.db_path = resource_path("items_data.json")
        self.images_dir = resource_path("image")

        self.current_category = "Все"
        self.current_search = ""
        self.current_sort = "По имени (А-Я)"
        self.image_cache = {}

        self.items = self._load_database()
        self.filtered_items = []
        self.displayed_count = 0
        self._search_job = None

        self._build_ui()
        self._apply_filters_and_render()

    def _load_database(self):
        items = []
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    items = json.load(f)
            except Exception as e:
                print(f"[ERROR] items_data.json: {e}")

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
        # Панель поиска и фильтров
        self.top_frame = ctk.CTkFrame(self, height=54, fg_color="#181a1f", corner_radius=0)
        self.top_frame.pack(fill="x", side="top")

        self.search_entry = ctk.CTkEntry(
            self.top_frame,
            placeholder_text="Поиск предмета...",
            width=220,
            height=34,
            corner_radius=6
        )
        self.search_entry.pack(side="left", padx=(15, 8), pady=10)
        self.search_entry.bind("<KeyRelease>", self._on_search_keypress)

        self.sort_var = ctk.StringVar(value="По имени (А-Я)")
        self.sort_menu = ctk.CTkOptionMenu(
            self.top_frame,
            values=["По имени (А-Я)", "По имени (Я-А)", "По категории"],
            command=self._on_sort_changed,
            variable=self.sort_var,
            width=150,
            height=32,
            fg_color="#232730",
            button_color="#2b313d",
            button_hover_color="#3a4252"
        )
        self.sort_menu.pack(side="left", padx=(0, 10), pady=10)

        categories = ["Все", "★ Избранное", "Оружие", "Броня", "Артефакты", "Обвесы", "Разное"]
        self.cat_buttons = []

        for cat in categories:
            btn = ctk.CTkButton(
                self.top_frame,
                text=cat,
                width=80 if len(cat) < 8 else 95,
                height=32,
                corner_radius=6,
                fg_color="#278191" if cat == "Все" else "#232730",
                hover_color="#1e6572",
                command=lambda c=cat: self._set_category(c)
            )
            btn.pack(side="left", padx=2, pady=10)
            self.cat_buttons.append(btn)

        # Скролл списка
        self.items_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.items_scroll.pack(fill="both", expand=True, padx=15, pady=8)

        # Глобальный бинд скролла мыши для фикса бага застревания колесика
        self._bind_mouse_wheel(self.items_scroll)

    def _bind_mouse_wheel(self, widget):
        """Рекурсивно привязывает события колесика мыши к холсту"""
        def _on_mousewheel(event):
            # Поддержка Windows / Linux
            delta = -1 * int(event.delta / 120) if event.delta else 0
            if delta != 0:
                self.items_scroll._parent_canvas.yview_scroll(delta, "units")
            return "break"

        widget.bind("<MouseWheel>", _on_mousewheel, add="+")
        for child in widget.winfo_children():
            child.bind("<MouseWheel>", _on_mousewheel, add="+")

    def _set_category(self, cat_name: str):
        self.current_category = cat_name
        for btn in self.cat_buttons:
            btn.configure(fg_color="#278191" if btn.cget("text") == cat_name else "#232730")
        self._apply_filters_and_render()

    def _on_search_keypress(self, event=None):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(200, self._trigger_search)

    def _trigger_search(self):
        self.current_search = self.search_entry.get().strip().lower()
        self._apply_filters_and_render()

    def _on_sort_changed(self, choice):
        self.current_sort = choice
        self._apply_filters_and_render()

    def _apply_filters_and_render(self):
        mapping = CATEGORY_MAPPING.get(self.current_category, "Все")
        favorites = set(get_favorites())

        filtered = []
        for it in self.items:
            name = str(it.get("name", ""))
            category = str(it.get("category", "")).lower()
            item_id = str(it.get("id"))

            if self.current_search and self.current_search not in name.lower():
                continue

            if self.current_category == "★ Избранное":
                if item_id not in favorites:
                    continue
            elif self.current_category != "Все":
                if isinstance(mapping, list):
                    if not any(sub in category for sub in mapping):
                        continue

            filtered.append(it)

        if self.current_sort == "По имени (А-Я)":
            filtered.sort(key=lambda x: str(x.get("name", "")).lower())
        elif self.current_sort == "По имени (Я-А)":
            filtered.sort(key=lambda x: str(x.get("name", "")).lower(), reverse=True)
        elif self.current_sort == "По категории":
            filtered.sort(key=lambda x: (str(x.get("category", "")), str(x.get("name", ""))))

        self.filtered_items = filtered

        for w in self.items_scroll.winfo_children():
            w.destroy()

        self.displayed_count = 0
        self._render_next_batch()

    def _render_next_batch(self):
        next_items = self.filtered_items[self.displayed_count : self.displayed_count + ITEMS_PER_PAGE]
        if not next_items:
            if self.displayed_count == 0:
                empty = ctk.CTkLabel(self.items_scroll, text="Ничего не найдено", font=("Segoe UI", 14), text_color="#777")
                empty.pack(pady=40)
            return

        favorites = set(get_favorites())

        if hasattr(self, "load_more_btn") and self.load_more_btn and self.load_more_btn.winfo_exists():
            self.load_more_btn.destroy()

        for it in next_items:
            self._render_item_row(it, is_fav=(str(it.get("id")) in favorites))

        self.displayed_count += len(next_items)

        if self.displayed_count < len(self.filtered_items):
            rem = len(self.filtered_items) - self.displayed_count
            self.load_more_btn = ctk.CTkButton(
                self.items_scroll,
                text=f"Загрузить ещё... (осталось {rem})",
                height=36,
                fg_color="#1f232b",
                hover_color="#2b313d",
                command=self._render_next_batch
            )
            self.load_more_btn.pack(fill="x", pady=10, padx=20)
            self._bind_mouse_wheel(self.load_more_btn)

    def _render_item_row(self, it: dict, is_fav: bool):
        row = ctk.CTkFrame(self.items_scroll, height=52, fg_color="#1a1d24", corner_radius=6)
        row.pack(fill="x", pady=2, padx=4)

        item_id = str(it.get("id"))

        fav_btn = ctk.CTkButton(
            row,
            text="★" if is_fav else "☆",
            width=32,
            height=32,
            font=("Segoe UI", 14),
            fg_color="transparent",
            text_color="#f1c40f" if is_fav else "#555555",
            hover_color="#232832"
        )
        fav_btn.configure(command=lambda i_id=item_id, btn=fav_btn: self._on_toggle_fav(i_id, btn))
        fav_btn.pack(side="left", padx=(8, 2))

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
            img_lbl = ctk.CTkLabel(row, text="", image=img_ctk)
            img_lbl.pack(side="left", padx=(4, 6))

        name_lbl = ctk.CTkLabel(
            row,
            text=it.get("name", "Без названия"),
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        )
        name_lbl.pack(side="left", fill="x", expand=True, padx=8)

        cat_lbl = ctk.CTkLabel(
            row,
            text=str(it.get("category", "")).capitalize(),
            font=("Segoe UI", 11),
            text_color="#7f8c8d",
            width=100,
            anchor="e"
        )
        cat_lbl.pack(side="left", padx=8)

        view_btn = ctk.CTkButton(
            row,
            text="Просмотреть",
            width=100,
            height=30,
            font=("Segoe UI", 12, "bold"),
            fg_color="#278191",
            hover_color="#1e6572",
            command=lambda item=it: self.on_open_detail(item)
        )
        view_btn.pack(side="right", padx=(8, 12))

        del_btn = ctk.CTkButton(
            row,
            text="✕",
            width=26,
            height=26,
            font=("Segoe UI", 11),
            fg_color="transparent",
            text_color="#555555",
            hover_color="#3a1c1c",
            command=lambda item=it, r_widget=row: self._delete_item(item, r_widget)
        )
        del_btn.pack(side="right", padx=(0, 4))

        # Привязываем колесико мыши к строке и её дочерним виджетам
        self._bind_mouse_wheel(row)

    def _on_toggle_fav(self, item_id: str, btn: ctk.CTkButton):
        is_fav = toggle_favorite(item_id)
        btn.configure(
            text="★" if is_fav else "☆",
            text_color="#f1c40f" if is_fav else "#555555"
        )
        if self.current_category == "★ Избранное":
            self._apply_filters_and_render()

    def _delete_item(self, item: dict, row_widget):
        item_id = str(item.get("id"))
        add_deleted_item(item_id)
        self.items = [i for i in self.items if str(i.get("id")) != item_id]
        self.filtered_items = [i for i in self.filtered_items if str(i.get("id")) != item_id]
        row_widget.destroy()