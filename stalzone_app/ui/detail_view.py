import customtkinter as ctk

class DetailView(ctk.CTkFrame):
    def __init__(self, master, on_back):
        super().__init__(master, fg_color="transparent")
        self.on_back = on_back

        self.sample_prices = [1600, 1550, 1520, 1570, 1490, 1420, 1450, 1400]
        self._current_mode = "50/50"

        self._build_ui()

    def _build_ui(self):
        # 1. Верхняя панель навигации
        top_bar = ctk.CTkFrame(self, height=48, corner_radius=0)
        top_bar.pack(fill="x")

        ctk.CTkButton(
            top_bar,
            text="← Назад к лотам",
            width=120,
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color="#444",
            command=self.on_back
        ).pack(side="left", padx=14, pady=8)

        self.title_lbl = ctk.CTkLabel(top_bar, text="", font=("Segoe UI", 15, "bold"))
        self.title_lbl.pack(side="left", padx=10)

        # Переключатель раскладки колонок в шапке
        mode_box = ctk.CTkFrame(top_bar, fg_color="#181a20", corner_radius=6)
        mode_box.pack(side="right", padx=14, pady=8)

        ctk.CTkLabel(mode_box, text="Вид:", font=("Segoe UI", 11), text_color="#888").pack(side="left", padx=(8, 4))

        self.btn_lots = ctk.CTkButton(
            mode_box, text="Лоты", width=55, height=26,
            fg_color="transparent", text_color="#aaa", hover_color="#232730",
            font=("Segoe UI", 11), command=lambda: self.set_layout("lots")
        )
        self.btn_lots.pack(side="left", padx=2, pady=2)

        self.btn_mid = ctk.CTkButton(
            mode_box, text="50 / 50", width=65, height=26,
            fg_color="#278191", text_color="#fff", hover_color="#1e6572",
            font=("Segoe UI", 11, "bold"), command=lambda: self.set_layout("50/50")
        )
        self.btn_mid.pack(side="left", padx=2, pady=2)

        self.btn_chart = ctk.CTkButton(
            mode_box, text="График", width=65, height=26,
            fg_color="transparent", text_color="#aaa", hover_color="#232730",
            font=("Segoe UI", 11), command=lambda: self.set_layout("chart")
        )
        self.btn_chart.pack(side="left", padx=(2, 4), pady=2)

        # 2. Главная область на GRID с процентными долями
        self.main_layout = ctk.CTkFrame(self, fg_color="transparent")
        self.main_layout.pack(fill="both", expand=True, padx=10, pady=10)

        self.main_layout.grid_rowconfigure(0, weight=1)
        self.main_layout.grid_columnconfigure(0, weight=5, uniform="group1")  # Левая (лоты)
        self.main_layout.grid_columnconfigure(1, weight=5, uniform="group1")  # Правая (график)

        # ЛЕВАЯ ПАНЕЛЬ
        self.left_panel = ctk.CTkFrame(self.main_layout, corner_radius=8)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        ctk.CTkLabel(
            self.left_panel,
            text="ТЕКУЩИЕ ЛОТЫ В ИГРЕ (API)",
            font=("Segoe UI", 12, "bold"),
            text_color="#2fbcd4"
        ).pack(anchor="w", padx=14, pady=(10, 6))

        self.scroll_lots = ctk.CTkScrollableFrame(self.left_panel, corner_radius=6)
        self.scroll_lots.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ПРАВАЯ ПАНЕЛЬ
        self.right_panel = ctk.CTkFrame(self.main_layout, corner_radius=8)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        stats_box = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        stats_box.pack(fill="x", padx=10, pady=(10, 8))

        day_details = {"Минимальная цена:": "1 380 Р", "Максимальная цена:": "1 510 Р", "Продано за 24ч:": "14 шт."}
        self.card_day = self._make_price_badge(stats_box, "Средняя цена за ДЕНЬ", "1 420 Р", "#2ecc71", day_details)
        self.card_day.pack(fill="x", pady=(0, 5))

        week_details = {"Мин. за неделю:": "1 250 Р", "Макс. за неделю:": "1 690 Р", "Всего продаж:": "89 шт."}
        self.card_week = self._make_price_badge(stats_box, "Средняя цена за НЕДЕЛЮ", "1 490 Р", "#3498db", week_details)
        self.card_week.pack(fill="x", pady=(0, 5))

        month_details = {"Мин. за месяц:": "1 100 Р", "Макс. за месяц:": "1 950 Р", "Всего продаж:": "412 шт."}
        self.card_month = self._make_price_badge(stats_box, "Средняя цена за МЕСЯЦ", "1 580 Р", "#f1c40f", month_details)
        self.card_month.pack(fill="x")

        # График
        chart_panel = ctk.CTkFrame(self.right_panel, corner_radius=8, fg_color="#181a20")
        chart_panel.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        ctk.CTkLabel(
            chart_panel,
            text="ГРАФИК ДИНАМИКИ ЦЕН",
            font=("Segoe UI", 12, "bold"),
            text_color="#888888"
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self.chart_canvas = ctk.CTkCanvas(chart_panel, bg="#181a20", highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.chart_canvas.bind("<Configure>", lambda e: self._draw_chart(self.sample_prices))

    # ==========================================
    # УПРАВЛЕНИЕ РЕЖИМАМИ РАСКЛАДКИ
    # ==========================================
    def set_layout(self, mode: str):
        self._current_mode = mode

        # Сброс стилей кнопок
        for b in [self.btn_lots, self.btn_mid, self.btn_chart]:
            b.configure(fg_color="transparent", text_color="#aaa")

        if mode == "lots":
            self.btn_lots.configure(fg_color="#278191", text_color="#fff")
            # 65% лоты, 35% график
            self.main_layout.grid_columnconfigure(0, weight=65)
            self.main_layout.grid_columnconfigure(1, weight=35)
        elif mode == "chart":
            self.btn_chart.configure(fg_color="#278191", text_color="#fff")
            # 35% лоты, 65% график
            self.main_layout.grid_columnconfigure(0, weight=35)
            self.main_layout.grid_columnconfigure(1, weight=65)
        else:
            self.btn_mid.configure(fg_color="#278191", text_color="#fff")
            # 50% на 50%
            self.main_layout.grid_columnconfigure(0, weight=50)
            self.main_layout.grid_columnconfigure(1, weight=50)

        # Перерисовываем холст под новые пропорции
        self.after(20, lambda: self._draw_chart(self.sample_prices))

    # ==========================================
    # ДАННЫЕ И ВИДЖЕТЫ
    # ==========================================
    def show_item(self, item: dict):
        self.title_lbl.configure(text=f"Аналитика: «{item['name']}»")
        for w in self.scroll_lots.winfo_children():
            w.destroy()

        mock_lots = [
            {"price": 1488, "count": "1 шт.", "time": "2 ч."},
            {"price": 1488, "count": "3 шт.", "time": "5 ч."},
            {"price": 1488, "count": "1 шт.", "time": "12 ч."},
            {"price": 1488, "count": "5 шт.", "time": "1 дн."},
            {"price": 1488, "count": "2 шт.", "time": "2 дн."},
        ]
        for lot in mock_lots:
            row = ctk.CTkFrame(self.scroll_lots, height=36, corner_radius=5)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=f"Цена: {lot['price']:,} ₽".replace(",", " "), font=("Segoe UI", 12, "bold"), text_color="#f1c40f").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"Кол-во: {lot['count']}", font=("Segoe UI", 11), text_color="#bbbbbb").pack(side="left", padx=12)
            ctk.CTkLabel(row, text=f"Осталось: {lot['time']}", font=("Segoe UI", 11), text_color="#777777").pack(side="right", padx=10)

    def _make_price_badge(self, parent, title, val, color, details):
        card = ctk.CTkFrame(parent, corner_radius=6)

        hdr = ctk.CTkFrame(card, fg_color="transparent", height=40, cursor="hand2")
        hdr.pack(fill="x", padx=8, pady=2)

        arrow = ctk.CTkLabel(hdr, text="▼", font=("Segoe UI", 10), text_color="#777777")
        arrow.pack(side="left", padx=(4, 6))

        title_lbl = ctk.CTkLabel(hdr, text=title, font=("Segoe UI", 11), text_color="#aaaaaa")
        title_lbl.pack(side="left")

        val_lbl = ctk.CTkLabel(hdr, text=val, font=("Segoe UI", 13, "bold"), text_color=color)
        val_lbl.pack(side="right", padx=6)

        dframe = ctk.CTkFrame(card, fg_color="#181a21", corner_radius=5)
        for k, v in details.items():
            r = ctk.CTkFrame(dframe, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(r, text=k, font=("Segoe UI", 10), text_color="#888888").pack(side="left")
            ctk.CTkLabel(r, text=v, font=("Segoe UI", 10, "bold"), text_color="#cccccc").pack(side="right")

        card.is_exp = False

        def toggle(event=None):
            if card.is_exp:
                dframe.pack_forget()
                arrow.configure(text="▼")
                card.is_exp = False
            else:
                dframe.pack(fill="x", padx=8, pady=(0, 6))
                arrow.configure(text="▲")
                card.is_exp = True

        for w in [card, hdr, arrow, title_lbl, val_lbl]:
            w.bind("<Button-1>", toggle)

        return card

    def _draw_chart(self, prices):
        c = self.chart_canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 40 or h < 40 or len(prices) < 2:
            return

        px, py = 20, 15
        diff = max(1, max(prices) - min(prices))
        pts = [(px + i * ((w - 2 * px) / (len(prices) - 1)), h - py - ((p - min(prices)) / diff) * (h - 2 * py)) for i, p in enumerate(prices)]

        for f in [0.25, 0.5, 0.75]:
            c.create_line(px, h * f, w - px, h * f, fill="#252934", width=1)

        for i in range(len(pts) - 1):
            c.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill="#278191", width=2, smooth=True)

        for x, y in pts:
            c.create_oval(x - 2.5, y - 2.5, x + 2.5, y + 2.5, fill="#2fbcd4", outline="#ffffff", width=1)