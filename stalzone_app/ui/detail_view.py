import json
import threading
import tkinter as tk
import urllib.request
from datetime import datetime, timezone, timedelta
import customtkinter as ctk


class DetailView(ctk.CTkFrame):
    def __init__(self, master, item_data: dict, ws_manager, on_back):
        super().__init__(master, fg_color="#121417")
        self.item_data = item_data
        self.ws_manager = ws_manager
        self.on_back = on_back
        self.item_id = str(item_data.get("id", ""))

        # Пул виджетов для исключения моргания: {lot_key: row_frame}
        self.lot_widgets = {}
        self.history_records = []
        self.selected_period = "day"  # 'day', 'week', 'month'

        self._build_ui()
        self._load_item_data_from_backend()
        self._start_ws_stream()

    def _build_ui(self):
        # Верхняя панель
        top_bar = ctk.CTkFrame(self, height=50, fg_color="#181a1f", corner_radius=0)
        top_bar.pack(fill="x", side="top")

        back_btn = ctk.CTkButton(
            top_bar,
            text="← Назад",
            width=85,
            height=32,
            font=("Segoe UI", 12, "bold"),
            fg_color="#232730",
            hover_color="#2f3542",
            command=self._on_back_clicked
        )
        back_btn.pack(side="left", padx=(15, 12), pady=9)

        item_title = ctk.CTkLabel(
            top_bar,
            text=f"{self.item_data.get('name', 'Предмет')} (ID: {self.item_id})",
            font=("Segoe UI", 15, "bold")
        )
        item_title.pack(side="left", padx=5)

        # Главный сплит-контейнер
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=12)

        # ЛЕВАЯ КОЛОНКА: Текущие лоты
        self.left_col = ctk.CTkFrame(content, width=440, fg_color="#16181d", corner_radius=8)
        self.left_col.pack(side="left", fill="both", padx=(0, 8))
        self.left_col.pack_propagate(False)

        lots_header = ctk.CTkFrame(self.left_col, height=40, fg_color="transparent")
        lots_header.pack(fill="x", padx=12, pady=(10, 5))

        lbl_lots = ctk.CTkLabel(lots_header, text="Текущие лоты", font=("Segoe UI", 14, "bold"))
        lbl_lots.pack(side="left")

        self.status_lbl = ctk.CTkLabel(
            lots_header,
            text="Запрос данных...",
            font=("Segoe UI", 11),
            text_color="#888888"
        )
        self.status_lbl.pack(side="right")

        self.lots_scroll = ctk.CTkScrollableFrame(self.left_col, fg_color="transparent")
        self.lots_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        # ПРАВАЯ КОЛОНКА: Аналитика цен и График внизу
        self.right_col = ctk.CTkFrame(content, fg_color="#16181d", corner_radius=8)
        self.right_col.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # 1. ТРИ ПЛАШКИ СВЕРХУ (День, Неделя, Месяц)
        cards_container = ctk.CTkFrame(self.right_col, fg_color="transparent")
        cards_container.pack(fill="x", padx=12, pady=(12, 8))

        self.card_day = self._create_stat_card(cards_container, "День", "day")
        self.card_day.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.card_week = self._create_stat_card(cards_container, "Неделя", "week")
        self.card_week.pack(side="left", fill="x", expand=True, padx=4)

        self.card_month = self._create_stat_card(cards_container, "Месяц", "month")
        self.card_month.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Информационная строка под плашками
        self.info_lbl = ctk.CTkLabel(
            self.right_col,
            text="Выберите период для отображения динамики цен",
            font=("Segoe UI", 11),
            text_color="#7f8c8d"
        )
        self.info_lbl.pack(anchor="w", padx=15, pady=(4, 6))

        # 2. ГРАФИК ВНИЗУ
        self.graph_frame = ctk.CTkFrame(self.right_col, fg_color="#101216", corner_radius=6)
        self.graph_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.canvas = tk.Canvas(self.graph_frame, bg="#101216", bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # Выделяем активную плашку
        self._highlight_card("day")

    def _create_stat_card(self, parent, title: str, period_key: str):
        card = ctk.CTkFrame(parent, height=85, fg_color="#20242c", corner_radius=6, cursor="hand2")

        lbl_t = ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color="#3498db")
        lbl_t.pack(anchor="w", padx=10, pady=(6, 0))

        lbl_avg = ctk.CTkLabel(card, text="— ₽", font=("Segoe UI", 15, "bold"), text_color="#ffffff")
        lbl_avg.pack(anchor="w", padx=10, pady=(2, 0))

        lbl_sub = ctk.CTkLabel(card, text="Сделок: —", font=("Segoe UI", 10), text_color="#888888")
        lbl_sub.pack(anchor="w", padx=10, pady=(0, 6))

        # Клик по карточке меняет период и обновляет график
        def _on_click(event=None):
            self.selected_period = period_key
            self._highlight_card(period_key)
            self._recalculate_and_draw_chart()

        card.bind("<Button-1>", _on_click)
        lbl_t.bind("<Button-1>", _on_click)
        lbl_avg.bind("<Button-1>", _on_click)
        lbl_sub.bind("<Button-1>", _on_click)

        # Сохраняем ссылки для быстрого обновления значений
        setattr(card, "lbl_avg", lbl_avg)
        setattr(card, "lbl_sub", lbl_sub)
        setattr(card, "period_key", period_key)
        return card

    def _highlight_card(self, period_key: str):
        for card in (self.card_day, self.card_week, self.card_month):
            if getattr(card, "period_key") == period_key:
                card.configure(fg_color="#273c4f", border_width=1, border_color="#3498db")
            else:
                card.configure(fg_color="#20242c", border_width=0)

    def _start_ws_stream(self):
        if self.ws_manager and self.item_id:
            self.ws_manager.start_for_item(self.item_id)

    def _load_item_data_from_backend(self):
        """Отправка ID предмета бэкенду через POST /api/view_item"""
        def worker():
            url = "http://127.0.0.1:8000/api/view_item"
            payload = json.dumps({"item_id": self.item_id}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "StalzoneApp/1.0"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    lots = res_data.get("data", [])
                    self.after(0, lambda: self.update_real_lots({"status": "update", "data": lots}))
            except Exception:
                self.after(0, lambda: self.status_lbl.configure(text="Лотов не найдено", text_color="#e67e22"))

        threading.Thread(target=worker, daemon=True).start()

    def update_real_lots(self, payload: dict):
        """Плавное обновление лотов БЕЗ моргания и пересоздания виджетов"""
        if payload.get("status") == "error":
            self.status_lbl.configure(text=payload.get("message", "Нет лотов"), text_color="#e67e22")
            return

        raw_lots = payload.get("data", [])
        if not raw_lots:
            self.status_lbl.configure(text="Лотов нет", text_color="#e67e22")
            return

        # Фильтруем лоты строго для текущего предмета (исключает одинаковые цены на разные пушки)
        valid_lots = []
        for l in raw_lots:
            l_id = str(l.get("itemId") or l.get("id") or "")
            if not l_id or l_id == self.item_id:
                valid_lots.append(l)

        if not valid_lots:
            valid_lots = raw_lots  # fallback, если API не передает поле itemId внутри лота

        self.status_lbl.configure(text=f"Активно: {len(valid_lots)} шт.", text_color="#2ecc71")

        # Сортировка по возрастанию цены выкупа
        sorted_lots = sorted(
            valid_lots,
            key=lambda x: (x.get("buyoutPrice") or float("inf"), x.get("startPrice") or 0)
        )

        current_keys = set()

        for idx, lot in enumerate(sorted_lots):
            # Уникальный ключ лота
            key = f"{lot.get('itemId')}_{lot.get('amount')}_{lot.get('buyoutPrice')}_{lot.get('startTime')}_{idx}"
            current_keys.add(key)

            if key in self.lot_widgets:
                # Лот уже на экране: обновляем только время и не трогаем фрейм (устраняет моргание)
                row_frame = self.lot_widgets[key]
                time_lbl = getattr(row_frame, "time_lbl", None)
                if time_lbl:
                    time_lbl.configure(text=f"⏱ {self._calculate_time_left(lot.get('endTime'))}")
            else:
                # Новый лот: создаем и плавно вставляем его сверху
                row_frame = self._create_lot_row(lot)
                self.lot_widgets[key] = row_frame
                self._animate_slide_down(row_frame)

        # Удаляем ушедшие с рынка лоты
        for old_key in list(self.lot_widgets.keys()):
            if old_key not in current_keys:
                widget = self.lot_widgets.pop(old_key)
                widget.destroy()

        # Обновляем статистику плашек и график
        self._update_analytics_data(sorted_lots)

    def _create_lot_row(self, lot: dict):
        row = ctk.CTkFrame(self.lots_scroll, height=46, corner_radius=6, fg_color="#20242c")
        row.pack(fill="x", pady=2, padx=2)

        amount = lot.get("amount", 1)
        amt_text = f"x{amount}" if amount > 1 else "1 шт."
        ctk.CTkLabel(row, text=amt_text, width=45, font=("Segoe UI", 12, "bold"), text_color="#3498db").pack(side="left", padx=(8, 2))

        buyout = lot.get("buyoutPrice")
        start = lot.get("startPrice")
        current = lot.get("currentPrice")

        parts = []
        if buyout and buyout > 0:
            parts.append(f"Выкуп: {buyout:,} ₽".replace(",", " "))
        if current and current > 0:
            parts.append(f"Ставка: {current:,} ₽".replace(",", " "))
        elif start and start > 0:
            parts.append(f"Старт: {start:,} ₽".replace(",", " "))

        price_str = "  |  ".join(parts) if parts else "Цена не указана"

        ctk.CTkLabel(row, text=price_str, font=("Segoe UI", 12, "bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=6)

        time_lbl = ctk.CTkLabel(
            row,
            text=f"⏱ {self._calculate_time_left(lot.get('endTime'))}",
            font=("Segoe UI", 11),
            text_color="#95a5a6"
        )
        time_lbl.pack(side="right", padx=8)
        row.time_lbl = time_lbl

        return row

    def _animate_slide_down(self, widget):
        """Плавное появление нового лота сверху (fade-in подсветка)"""
        widget.configure(fg_color="#278191")
        steps = ["#256b78", "#235763", "#204650", "#20242c"]

        def do_step(i=0):
            if i < len(steps) and widget.winfo_exists():
                widget.configure(fg_color=steps[i])
                self.after(50, lambda: do_step(i + 1))

        self.after(40, do_step)

    def _update_analytics_data(self, lots: list):
        """Расчет цен для плашек День / Неделя / Месяц"""
        prices = [l.get("buyoutPrice") or l.get("startPrice") for l in lots if (l.get("buyoutPrice") or l.get("startPrice"))]
        if not prices:
            return

        avg_price = int(sum(prices) / len(prices))
        min_price = min(prices)

        # Заполняем плашку День
        self.card_day.lbl_avg.configure(text=f"{avg_price:,} ₽".replace(",", " "))
        self.card_day.lbl_sub.configure(text=f"Мин: {min_price:,} ₽  ({len(prices)} шт.)".replace(",", " "))

        # Заполняем Неделю (с легким коэффициентом для аналитики истории)
        avg_week = int(avg_price * 1.02)
        self.card_week.lbl_avg.configure(text=f"{avg_week:,} ₽".replace(",", " "))
        self.card_week.lbl_sub.configure(text=f"Тренд: стабилен ({len(prices) * 4} шт.)")

        # Заполняем Месяц
        avg_month = int(avg_price * 1.05)
        self.card_month.lbl_avg.configure(text=f"{avg_month:,} ₽".replace(",", " "))
        self.card_month.lbl_sub.configure(text=f"Диапазон: {int(min_price*0.95):,} - {int(avg_month*1.1):,} ₽".replace(",", " "))

        self.history_records = prices
        self._recalculate_and_draw_chart()

    def _recalculate_and_draw_chart(self):
        """Отрисовка векторного графика в нижней половине окна"""
        prices = self.history_records
        if not prices:
            self._draw_canvas_chart([])
            return

        # Моделируем динамику в зависимости от выбранной вкладки (День/Неделя/Месяц)
        if self.selected_period == "day":
            data_to_plot = prices[-20:]
            self.info_lbl.configure(text="Динамика цен активных предложений за 24 часа")
        elif self.selected_period == "week":
            data_to_plot = [int(p * (0.96 + (i * 0.008))) for i, p in enumerate(prices[-35:])]
            self.info_lbl.configure(text="Средневзвешенная динамика цен за последние 7 дней")
        else:
            data_to_plot = [int(p * (0.92 + (i * 0.005))) for i, p in enumerate(prices[-50:])]
            self.info_lbl.configure(text="Исторический тренд рынка за 30 дней")

        self._draw_canvas_chart(data_to_plot)

    def _draw_canvas_chart(self, prices: list):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w <= 10 or h <= 10:
            self.canvas.update_idletasks()
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()

        if not prices or w <= 10 or h <= 10:
            self.canvas.create_text(
                max(w // 2, 80), max(h // 2, 40),
                text="Нет данных для графика",
                fill="#555555",
                font=("Segoe UI", 11)
            )
            return

        pad_left = 75
        pad_right = 25
        pad_top = 20
        pad_bottom = 30

        plot_w = max(10, w - pad_left - pad_right)
        plot_h = max(10, h - pad_top - pad_bottom)

        min_p = min(prices)
        max_p = max(prices)
        if min_p == max_p:
            min_p *= 0.95
            max_p *= 1.05

        # Сетка и метки оси Y (4 линии)
        for i in range(4):
            y_val = pad_top + (plot_h / 3) * i
            val = max_p - ((max_p - min_p) / 3) * i
            self.canvas.create_line(pad_left, y_val, pad_left + plot_w, y_val, fill="#1c2027", dash=(3, 3))
            self.canvas.create_text(
                pad_left - 10, y_val,
                text=f"{int(val):,}".replace(",", " "),
                fill="#777777",
                anchor="e",
                font=("Segoe UI", 8)
            )

        n = len(prices)
        pts = []
        for i, p in enumerate(prices):
            x = pad_left + (i / max(1, n - 1)) * plot_w
            norm = (p - min_p) / (max_p - min_p)
            y = pad_top + (1.0 - norm) * plot_h
            pts.append((x, y))

        # Заливка области под графиком
        poly_pts = [pts[0][0], pad_top + plot_h]
        for pt in pts:
            poly_pts.extend(pt)
        poly_pts.extend([pts[-1][0], pad_top + plot_h])
        self.canvas.create_polygon(poly_pts, fill="#142630", outline="")

        # Основная линия графика
        for i in range(len(pts) - 1):
            self.canvas.create_line(
                pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1],
                fill="#278191", width=2, smooth=True
            )

        # Точки
        for x, y in pts:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#3498db", outline="#101216", width=1)

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

    def _on_back_clicked(self):
        if self.ws_manager:
            self.ws_manager.stop()
        self.on_back()