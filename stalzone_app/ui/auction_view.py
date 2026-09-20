import os
import json
import customtkinter as ctk
from core.utils import load_item_icon, resource_path, get_app_dir
from core.config_manager import get_favorites, toggle_favorite, get_deleted_items, add_deleted_item
from core.api_client import notify_backend_item_viewed

# Словарь для точного сопоставления названий на кнопках с базой данных
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
    def __init__(self, master, on_open_detail):
        super().__init__(master, fg_color="transparent")
        self.on_open_detail = on_open_detail

        self.db_path = resource_path("items_data.json")
        self.items = self._load_database()
        self.favorites_set = set(get_favorites())

        self._rebuild_search_index()

        self.selected_category = "Все"
        self.filtered_items = self.items
        self.batch_size = 25
        self.current_loaded = 0

        self.card_pool = []
        self._search_timer = None

        self._build_ui()

    def _load_database(self):
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
            # Пропускаем удалённые через крестик
            if it.get("id") in deleted_set:
                continue

            # Исключаем категорию боеприпасов
            cat_lower = str(it.get("category", "")).lower()
            if any(kw in cat_lower for kw in ammo_keywords):
                continue

            active_items.append(it)

        return active_items

    def _save_database(self):
        try:
            real_db_path = os.path.join(get_app_dir(), "items_data.json")
            with open(real_db_path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, separators=(',', ':'))
        except Exception:
            pass

    def _rebuild_search_index(self):
        self.search_index = [
            (it, str(it.get("name", "")).lower(), str(it.get("category", "Разное")).strip().lower())
            for it in self.items
        ]

    def _build_ui(self):
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(fill="x")

        self.count_lbl = ctk.CTkLabel(
            top_bar,
            text=f"Торговая площадка ({len(self.items)} предм.)",
            font=("Segoe UI", 16, "bold")
        )
        self.count_lbl.pack(side="left", padx=20, pady=8)

        # Категории
        cats_bar = ctk.CTkFrame(self, fg_color="transparent")
        cats_bar.pack(fill="x", padx=20, pady=(6, 2))

        self.category_buttons = {}
        categories = ["Все", "★ Избранное", "Оружие", "Броня", "Артефакты", "Обвесы", "Разное"]

        for cat in categories:
            btn = ctk.CTkButton(
                cats_bar,
                text=cat,
                height=26,
                width=38,
                fg_color="#278191" if cat == "Все" else "#1f232b",
                hover_color="#1e6572" if cat == "Все" else "#2c323d",
                text_color="#ffffff" if cat == "Все" else "#aaaaaa",
                font=("Segoe UI", 11, "bold" if cat in ["Все", "★ Избранное"] else "normal"),
                command=lambda c=cat: self._on_select_category(c)
            )
            btn.pack(side="left", padx=(0, 6))
            self.category_buttons[cat] = btn

        # Поиск
        search_panel = ctk.CTkFrame(self, fg_color="transparent")
        search_panel.pack(fill="x", padx=20, pady=(4, 6))

        self.search_entry = ctk.CTkEntry(
            search_panel,
            placeholder_text="🔍 Поиск предмета по названию...",
            height=34,
            font=("Segoe UI", 12)
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_keypress)

        # Список карточек
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=6)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(2, 14))

        self.empty_lbl = ctk.CTkLabel(
            self.scroll,
            text="Ничего не найдено",
            text_color="#888888",
            font=("Segoe UI", 14)
        )

        self.load_more_btn = ctk.CTkButton(
            self.scroll,
            text="Показать ещё",
            height=32,
            fg_color="#1f232b",
            hover_color="#2c323d",
            command=self._render_next_batch
        )

        self._filter_and_apply()

    def _matches_category(self, item_cat_lower: str, selected_cat: str) -> bool:
        if selected_cat == "Все":
            return True
        keywords = CATEGORY_MAPPING.get(selected_cat, [selected_cat.lower()])
        return any(kw in item_cat_lower for kw in keywords)

    def _on_select_category(self, category):
        if self.selected_category == category:
            return
        self.selected_category = category
        for name, btn in self.category_buttons.items():
            if name == category:
                btn.configure(fg_color="#278191", text_color="#ffffff", hover_color="#1e6572")
            else:
                btn.configure(fg_color="#1f232b", text_color="#aaaaaa", hover_color="#2c323d")
        self._filter_and_apply()

    def _on_search_keypress(self, event=None):
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(180, self._filter_and_apply)

    def _filter_and_apply(self):
        query = self.search_entry.get().strip().lower()
        cat = self.selected_category

        results = []
        for item, name_lower, item_cat_lower in self.search_index:
            if cat == "★ Избранное":
                if item.get("id") not in self.favorites_set:
                    continue
            elif not self._matches_category(item_cat_lower, cat):
                continue

            if query and query not in name_lower:
                continue

            results.append(item)

        self._reset_and_render(results)

    def _get_or_create_card(self, index):
        if index < len(self.card_pool):
            return self.card_pool[index]

        card = ctk.CTkFrame(self.scroll, corner_radius=6, height=44)

        fav_btn = ctk.CTkButton(
            card,
            text="★",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#232731",
            text_color="#4a5568",
            font=("Segoe UI", 16, "bold")
        )
        fav_btn.pack(side="left", padx=(6, 4), pady=4)

        icon_lbl = ctk.CTkLabel(card, text="", width=36)
        icon_lbl.pack(side="left", padx=(0, 8), pady=4)

        title_lbl = ctk.CTkLabel(card, text="", font=("Segoe UI", 12, "bold"), anchor="w")
        title_lbl.pack(side="left", fill="x", expand=True, pady=4)

        del_btn = ctk.CTkButton(
            card,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#802b2b",
            text_color="#777777",
            font=("Segoe UI", 12, "bold")
        )
        del_btn.pack(side="right", padx=(4, 8), pady=4)

        btn = ctk.CTkButton(
            card,
            text="Просмотреть",
            width=92,
            height=28,
            fg_color="#278191",
            hover_color="#1e6572",
            font=("Segoe UI", 11, "bold")
        )
        btn.pack(side="right", padx=(0, 4), pady=4)

        card_data = {
            "frame": card,
            "fav_btn": fav_btn,
            "icon_lbl": icon_lbl,
            "title_lbl": title_lbl,
            "btn": btn,
            "del_btn": del_btn,
            "current_item": None
        }

        fav_btn.configure(command=lambda c=card_data: self._on_card_star_clicked(c))
        self.card_pool.append(card_data)
        return card_data

    def _delete_item(self, card, item):
        if not item or not isinstance(item, dict):
            return

        item_id = item.get("id")
        if not item_id:
            return

        # 1. Запоминаем в config.json
        add_deleted_item(item_id)

        # 2. Удаляем из списков в оперативной памяти
        self.items = [it for it in self.items if it.get("id") != item_id]
        self.filtered_items = [it for it in self.filtered_items if it.get("id") != item_id]
        self.favorites_set.discard(item_id)
        self._rebuild_search_index()
        self._save_database()

        # 3. Мгновенно скрываем карточку прямо на экране (скролл не сбивается!)
        if card and "frame" in card:
            card["frame"].pack_forget()

        # 4. Обновляем счётчики в шапке и на кнопке «Показать ещё»
        self.count_lbl.configure(text=f"Торговая площадка ({len(self.items)} предм.)")
        
        if hasattr(self, 'load_more_btn'):
            remains = len(self.filtered_items) - self.current_loaded
            if remains > 0:
                self.load_more_btn.configure(text=f"Показать ещё ({min(self.batch_size, remains)} из {remains})")
            else:
                self.load_more_btn.pack_forget()

    def _reset_and_render(self, item_list):
        try:
            self.scroll._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass
        self.filtered_items = item_list
        self.current_loaded = 0

        self.load_more_btn.pack_forget()
        self.empty_lbl.pack_forget()

        for c in self.card_pool:
            c["frame"].pack_forget()

        if not self.filtered_items:
            msg = "В избранном пока ничего нет" if self.selected_category == "★ Избранное" else "Ничего не найдено"
            self.empty_lbl.configure(text=msg)
            self.empty_lbl.pack(pady=40)
            return

        self._render_next_batch()

    def _render_next_batch(self):
        start = self.current_loaded
        end = min(start + self.batch_size, len(self.filtered_items))
        next_items = self.filtered_items[start:end]

        if not next_items:
            return

        self.load_more_btn.pack_forget()

        for i, item in enumerate(next_items):
            idx = start + i
            card = self._get_or_create_card(idx)
            card["current_item"] = item

            item_id = item.get("id", "")
            img = load_item_icon(item.get("icon", ""), size=(32, 32))
            if img:
                card["icon_lbl"].configure(image=img, text="")
                card["icon_lbl"].image = img
            else:
                card["icon_lbl"].configure(image="", text="📦")
                card["icon_lbl"].image = None

            card["title_lbl"].configure(text=f"{item.get('name', '')}  ·  {item.get('category', '')}")
            
            # Прямая привязка к текущему item без утечки замыканий
            card["btn"].configure(command=lambda it=item: self._on_item_view_clicked(it))
            card["del_btn"].configure(command=lambda c=card, it=item: self._delete_item(c, it))

            is_fav = item_id in self.favorites_set
            card["fav_btn"].configure(text_color="#f1c40f" if is_fav else "#4a5568")

            card["frame"].pack(fill="x", pady=2, padx=4)

        self.current_loaded = end

        if self.current_loaded < len(self.filtered_items):
            remains = len(self.filtered_items) - self.current_loaded
            self.load_more_btn.configure(text=f"Показать ещё ({min(self.batch_size, remains)} из {remains})")
            self.load_more_btn.pack(fill="x", pady=8, padx=20)

    def _on_card_star_clicked(self, card_data):
        item = card_data.get("current_item")
        if not item:
            return
        item_id = item.get("id")

        now_fav = toggle_favorite(item_id)
        if now_fav:
            self.favorites_set.add(item_id)
            card_data["fav_btn"].configure(text_color="#f1c40f")
        else:
            self.favorites_set.discard(item_id)
            card_data["fav_btn"].configure(text_color="#4a5568")

        if self.selected_category == "★ Избранное":
            self._filter_and_apply()

    def _on_item_view_clicked(self, item: dict):
        if item:
            notify_backend_item_viewed(item.get("id"))
            self.on_open_detail(item)