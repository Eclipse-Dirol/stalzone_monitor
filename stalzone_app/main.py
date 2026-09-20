import os
import customtkinter as ctk
from core.config_manager import load_config
from core.ws_client import WebSocketManager
from ui.welcome_view import WelcomeView
from ui.auction_view import AuctionView
from ui.detail_view import DetailView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stalzone Auction Client")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"[WARN] Не удалось установить ico: {e}")
        self.geometry("1100x680")
        self.minsize(960, 580)

        # Менеджер WebSocket (будет запускаться точечно под выбранный предмет)
        self.ws_manager = WebSocketManager(
            url="ws://127.0.0.1:8000/ws/auction",
            on_message_callback=self._handle_raw_ws_message
        )

        self.current_view = None
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # Проверка сохраненной авторизации
        config = load_config()
        if config.get("client_id") and config.get("client_secret"):
            self.on_login_success()
        else:
            self.show_welcome_view()

    def show_welcome_view(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = WelcomeView(master=self, on_login_success=self.on_login_success)
        self.current_view.pack(fill="both", expand=True)

    def show_auction_view(self):
        # Останавливаем сокет при возврате в каталог предметов
        self.ws_manager.stop()
        if self.current_view:
            self.current_view.destroy()
        self.current_view = AuctionView(master=self, on_open_detail=self.open_item_detail)
        self.current_view.pack(fill="both", expand=True)

    def open_item_detail(self, item_data: dict):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = DetailView(
            master=self,
            item_data=item_data,
            ws_manager=self.ws_manager,
            on_back=self.show_auction_view
        )
        self.current_view.pack(fill="both", expand=True)

    def on_login_success(self):
        self.show_auction_view()

    def _handle_raw_ws_message(self, payload):
        """Перенос сообщений в главный поток Tkinter"""
        self.after(0, lambda: self._process_ws_payload(payload))

    def _process_ws_payload(self, payload):
        if not isinstance(payload, dict):
            return

        # server_2.py отдает: {"status": "update", "data": ...} или {"status": "error", "message": "Нет лотов"}
        if isinstance(self.current_view, DetailView):
            self.current_view.update_real_lots(payload)

    def _on_close_window(self):
        self.ws_manager.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()