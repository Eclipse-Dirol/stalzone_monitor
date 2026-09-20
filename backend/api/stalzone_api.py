from scapi import AppClient, OAuthClient
import time
import logging
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
class SCAPI():
    def __init__(self):
        self.client = None

        self._is_token_ready = False

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

            client_id = config_data["client"]["CLIENT_ID"]
            client_secret = config_data["client"]["CLIENT_SECRET"]
            app_token = config_data["client"]["APP_TOKEN"]

            if app_token == "":
                authclient = OAuthClient(client_id=client_id, client_secret=client_secret)
                app_token_obj = await authclient.get_app_token()
                token = app_token_obj.access_token

                config_data["client"]["APP_TOKEN"] = token
                with open('config.json', "w", encoding="utf-8") as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)

                self.client = AppClient(token=token)
            else:
                self.client = AppClient(token=app_token)

            self._is_token_ready = True

    async def auction(self, item_id: str):
        t2 = time.perf_counter()
        await self._authorize()
        t3 = time.perf_counter()
        lots = await self.client.auction(item_id).lots(limit=1)
        t4 = time.perf_counter()
        print(f"[DEBUG] Запрос к аукциону: {t4 - t3:.3f} сек")

        return lots