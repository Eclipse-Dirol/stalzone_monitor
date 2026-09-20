import json
import threading
import time
import websocket


class WebSocketManager:
    def __init__(
        self,
        url="ws://127.0.0.1:8000/ws/auction",
        on_message_callback=None,
    ):
        self.url = url
        self.on_message_callback = on_message_callback
        self.ws = None
        self.thread = None
        self.is_running = False

    def start(self):
        """Запуск цикла WebSocket в отдельном потоке-демоне"""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        while self.is_running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                print(f"[WS /ws/auction] Ошибка соединения: {e}")

            # Автоматическая пауза перед повторной попыткой подключения
            if self.is_running:
                time.sleep(3)

    def _on_open(self, ws):
        print("[WS] Успешное подключение к /ws/auction")

    def _on_message(self, ws, message):
        try:
            payload = json.loads(message)
        except Exception:
            payload = message

        if self.on_message_callback:
            self.on_message_callback(payload)

    def _on_error(self, ws, error):
        print(f"[WS] Ошибка: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"[WS] Отключено от /ws/auction (код: {close_status_code})")

    def send_event(self, event_type: str, data: dict = None):
        """Отправка JSON данных на бэкенд в сокет аукциона"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            msg = json.dumps({"type": event_type, "data": data or {}})
            self.ws.send(msg)

    def stop(self):
        """Остановка фонового цикла"""
        self.is_running = False
        if self.ws:
            self.ws.close()