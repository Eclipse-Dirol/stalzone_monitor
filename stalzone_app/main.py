import os
import traceback
import customtkinter as ctk
from core.utils import resource_path
from ui.welcome_view import WelcomeView
from ui.auction_view import AuctionView
from ui.detail_view import DetailView
from core.api_client import init_backend_session
from core.ws_client import WebSocketManager

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Инициализация WS-клиента
        self.ws_manager = WebSocketManager(
            url="ws://127.0.0.1:8000/ws/auction",
            on_message_callback=self._handle_raw_ws_message,
        )

        # Корректное закрытие сокета при выходе из программы
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        self.title("Stalzone Auction")
        self.geometry("1100, 700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")

        # Иконка окна
        try:
            ico_path = resource_path("app_icon.ico")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
        except Exception:
            pass

        # Инициализация экранов с защитой от тихого падения
        try:
            self.welcome_screen = WelcomeView(self, on_login_success=self.show_auction)
            self.auction_screen = None
            self.detail_screen = DetailView(self, on_back=self.show_auction)

            # Однократная передача ключей бэкенду
            init_backend_session()

            self.show_welcome()
        except Exception as e:
            print(f"[FATAL ERROR] Ошибка запуска экранов: {e}")
            traceback.print_exc()

    def _hide_all(self):
        if hasattr(self, 'welcome_screen') and self.welcome_screen:
            self.welcome_screen.pack_forget()
        if hasattr(self, 'auction_screen') and self.auction_screen:
            self.auction_screen.pack_forget()
        if hasattr(self, 'detail_screen') and self.detail_screen:
            self.detail_screen.pack_forget()

    def show_welcome(self):
        self._hide_all()
        self.welcome_screen.pack(fill="both", expand=True)

    def show_auction(self):
        self._hide_all()
        try:
            if self.auction_screen is None:
                self.auction_screen = AuctionView(self, on_open_detail=self.show_detail)
            self.auction_screen.pack(fill="both", expand=True)
        except Exception as e:
            print(f"[ERROR] Ошибка открытия AuctionView: {e}")
            traceback.print_exc()

    def show_detail(self, item):
        self._hide_all()
        self.detail_screen.show_item(item)
        self.detail_screen.pack(fill="both", expand=True)

    def on_login_success(self):
        """Запускаем WebSocket только после успешного входа"""
        self.ws_manager.start()
        self.show_auction_view()

    def _handle_raw_ws_message(self, payload):
        # Безопасный перевод события из сетевого потока в главный поток GUI
        self.after(0, lambda: self._process_auction_ws_event(payload))

    def _process_ws_event(self, payload):
        """Обработка входящих данных в основном потоке"""
        print(f"[WS EVENT]: {payload}")

    def _on_close_window(self):
        self.ws_manager.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()