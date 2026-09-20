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
        self.item_id = None

    def start_for_item(self, item_id: str):
        """Запуск цикла WebSocket строго под выбранный item_id"""
        self.stop()
        self.item_id = str(item_id)
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            # Запуск соединения
            self.ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            print(f"[WS] Ошибка соединения: {e}")

    def _on_open(self, ws):
        # Сервер друга сразу ждет payload с item_id: config_data["item_id"]
        if self.item_id:
            msg = json.dumps({"item_id": self.item_id})
            ws.send(msg)

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
        pass

    def stop(self):
        """Полная остановка и закрытие сокета при выходе из предмета"""
        self.is_running = False
        self.item_id = None
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None