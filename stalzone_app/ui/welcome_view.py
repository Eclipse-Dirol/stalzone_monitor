import threading
import requests
import customtkinter as ctk
from core.config_manager import load_config, save_config

class WelcomeView(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.api_base_url = "http://127.0.0.1:8000"

        self._build_ui()
        self._start_fade_in()

    def _build_ui(self):
        saved_config = load_config()

        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.place(relx=0.5, rely=0.46, anchor="center")

        self.sub_title = ctk.CTkLabel(self.center_box, text="ДОБРО ПОЖАЛОВАТЬ В", font=("Segoe UI", 12, "bold"), text_color="#1a1a1a")
        self.sub_title.pack(pady=(0, 2))

        self.main_title = ctk.CTkLabel(self.center_box, text="АУКЦИОН STALZONE", font=("Segoe UI Black", 32, "bold"), text_color="#1a1a1a")
        self.main_title.pack(pady=(0, 24))

        self.client_id_entry = ctk.CTkEntry(self.center_box, placeholder_text="Введите Client ID", font=("Segoe UI", 13), width=320, height=40, corner_radius=8)
        self.client_id_entry.pack(pady=(0, 10))
        self._bind_clipboard(self.client_id_entry)
        if saved_config.get("client_id"):
            self.client_id_entry.insert(0, saved_config["client_id"])

        self.client_secret_entry = ctk.CTkEntry(self.center_box, placeholder_text="Введите Client Secret", show="•", font=("Segoe UI", 13), width=320, height=40, corner_radius=8)
        self.client_secret_entry.pack(pady=(0, 4))
        self._bind_clipboard(self.client_secret_entry)
        if saved_config.get("client_secret"):
            self.client_secret_entry.insert(0, saved_config["client_secret"])

        self.status_lbl = ctk.CTkLabel(self.center_box, text="", font=("Segoe UI", 11), text_color="#e74c3c", wraplength=320)
        self.status_lbl.pack(pady=(0, 8))

        self.enter_btn = ctk.CTkButton(self.center_box, text="ВОЙТИ", font=("Segoe UI", 14, "bold"), width=320, height=44, corner_radius=8, command=self._handle_login, fg_color="#1f232b", text_color="#333333", hover_color="#2980b9")
        self.enter_btn.pack()

        self.credits_lbl = ctk.CTkLabel(self, text="By: Cherry_Sport & MrYOSHIK", font=("Segoe UI", 14), text_color="#1a1a1a")
        self.credits_lbl.place(relx=0.98, rely=0.97, anchor="se")

    def _bind_clipboard(self, entry):
        def on_key_press(event):
            ctrl = (event.state & 4) != 0 or (event.state & 0x0004) != 0
            if ctrl and event.keycode == 86:
                try:
                    text = self.clipboard_get()
                    entry.insert("insert", text)
                except Exception:
                    pass
                return "break"
            elif ctrl and event.keycode == 65:
                entry.select_range(0, 'end')
                return "break"
        entry.bind("<KeyPress>", on_key_press, add="+")

    def _handle_login(self):
        cid = self.client_id_entry.get().strip()
        sec = self.client_secret_entry.get().strip()
        if not cid or not sec:
            self.status_lbl.configure(text="Заполните оба поля!", text_color="#e74c3c")
            return

        self.enter_btn.configure(state="disabled", text="АВТОРИЗАЦИЯ...")
        self.status_lbl.configure(text="Связь с сервером...", text_color="#3498db")

        def auth_worker():
            success = False
            err_text = "Не удалось подключиться к бэкенду"

            try:
                response = requests.post(
                    f"{self.api_base_url}/api/start",
                    json={"client_id": cid, "client_secret": sec},
                    timeout=5
                )

                data = response.json()

                if response.status_code == 200 and data.get("status") == "success":
                    success = True
                else:
                    detail = data.get("detail", {})
                    if isinstance(detail, dict):
                        err_text = detail.get("error_description") or detail.get("error") or "Неверные данные"
                    elif isinstance(detail, str):
                        err_text = detail
                    else:
                        err_text = "Ошибка авторизации"

            except requests.exceptions.ConnectionError:
                err_text = "Ошибка(Сервер не отвечает)"
            except Exception as e:
                err_text = f"Ошибка: {e}"

            # Возврат управления в интерфейс
            self.after(0, lambda: self._on_auth_completed(success, err_text, cid, sec))

        threading.Thread(target=auth_worker, daemon=True).start()

    def _on_auth_completed(self, success, err_text, cid, sec):
        self.enter_btn.configure(state="normal", text="ВОЙТИ")

        if not success:
            self.status_lbl.configure(text=f"✕ {err_text}", text_color="#e74c3c")
            return

        # Данные верны: сохраняем и входим
        self.status_lbl.configure(text="")
        save_config(cid, sec)
        self.on_login_success()

    def _start_fade_in(self):
        self.step = 0
        def step():
            self.step += 1
            t = min(1.0, self.step / 25)
            ease = 1 - pow(1 - t, 3)
            self.main_title.configure(text_color=self._interp("#1a1a1a", "#ffffff", ease))
            self.sub_title.configure(text_color=self._interp("#1a1a1a", "#3498db", ease))
            self.credits_lbl.configure(text_color=self._interp("#1a1a1a", "#666666", ease))
            btn_t = max(0.0, (ease - 0.25) / 0.75)
            self.enter_btn.configure(fg_color=self._interp("#1a1a1a", "#1f6aa5", btn_t), text_color=self._interp("#2a2a2a", "#ffffff", btn_t))
            if self.step < 25:
                self.after(16, step)
        step()

    @staticmethod
    def _interp(start, end, f):
        c1 = [int(start[i:i+2], 16) for i in (1, 3, 5)]
        c2 = [int(end[i:i+2], 16) for i in (1, 3, 5)]
        res = [int(c1[i] + (c2[i] - c1[i]) * f) for i in range(3)]
        return f"#{res[0]:02x}{res[1]:02x}{res[2]:02x}"