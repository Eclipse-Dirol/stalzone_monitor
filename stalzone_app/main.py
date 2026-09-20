import os
import traceback
import customtkinter as ctk
from core.utils import resource_path
from ui.welcome_view import WelcomeView
from ui.auction_view import AuctionView
from ui.detail_view import DetailView
from core.api_client import init_backend_session
from core.ws_client import WebSocketManager
from core.config_manager import load_config

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stalzone Auction Client")
        self.geometry("1100x680")
        self.minsize(960, 580)

        # Менеджер WebSocket к роуту /ws/auction
        self.ws_manager = WebSocketManager(
            url="ws://127.0.0.1:8000/ws/auction",
            on_message_callback=self._handle_raw_ws_message
        )

        self.current_view = None
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # Выбор стартового экрана в зависимости от наличия сохранённых ключей
        config = load_config()
        if config.get("client_id") and config.get("client_secret"):
            # Если ключи уже есть, сразу стартуем сокет и переходим к аукциону
            self.on_login_success()
        else:
            self.show_welcome_view()

    def show_welcome_view(self):
        if self.current_view:
            self.current_view.destroy()

        self.current_view = WelcomeView(master=self, on_login_success=self.on_login_success)
        self.current_view.pack(fill="both", expand=True)

    def show_auction_view(self):
        if self.current_view:
            self.current_view.destroy()

        self.current_view = AuctionView(master=self, ws_manager=self.ws_manager)
        self.current_view.pack(fill="both", expand=True)

    def on_login_success(self):
        """Успешный вход: подключаемся к сокету и открываем интерфейс аукциона"""
        self.ws_manager.start()
        self.show_auction_view()

    def _handle_raw_ws_message(self, payload):
        """Перенос входящих сообщений из потока сокета в поток UI"""
        self.after(0, lambda: self._process_ws_payload(payload))

    def _process_ws_payload(self, payload):
        """Передача полученного списка лотов в AuctionView"""
        if not isinstance(payload, dict):
            return

        if payload.get("status") == "success" and "data" in payload:
            if isinstance(self.current_view, AuctionView):
                self.current_view.update_real_lots(payload)

    def _on_close_window(self):
        """Остановка фоновых потоков при закрытии окна"""
        self.ws_manager.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()