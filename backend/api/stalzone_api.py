from scapi import AppClient, OAuthClient
import time
import logging
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
class SCAPI():
    def __init__(self):
        self._is_token_ready = False
        self.first_load = True
        self.active_lots = []

    async def start_desktop(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        client_id = config_data["client"]["CLIENT_ID"]
        client_secret = config_data["client"]["CLIENT_SECRET"]
        try:
            authclient = OAuthClient(client_id=client_id, client_secret=client_secret)
            app_token_obj = await authclient.get_app_token()
            token = app_token_obj.access_token
            config_data["client"]["APP_TOKEN"] = token
            with open('config.json', "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Лог авторизции: {e}")
            return False

    async def _authorize(self):
        if not self._is_token_ready:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            app_token = config_data["client"]["APP_TOKEN"]
            self.client = AppClient(token=app_token)

    async def request_for_auc(self, item_id: str, limit: int = 40):
        t2 = time.perf_counter()
        await self._authorize()
        t3 = time.perf_counter()
        lots = await self.client.auction(item_id).lots(limit=limit)
        t4 = time.perf_counter()
        print(f"[DEBUG] Авторизация: {t3 - t2:.3f} сек")
        print(f"[DEBUG] Запрос к аукциону: {t4 - t3:.3f} сек")

        return lots

    async def constant_loading(self, item_id: str):
        if self.first_load:

            self.active_lots = await self.request_for_auc(item_id)
            self.first_load = False

            return self.active_lots
        else:
            new_lots = await self.request_for_auc(item_id, limit=1)

            if new_lots:
                self.active_lots.insert(0, new_lots[0])
                if len(self.active_lots) > 40:
                    self.active_lots.pop()
            return self.active_lots