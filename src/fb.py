import httpx

from . import config


class Client:
    def __init__(self):
        self.cli = httpx.Client(base_url="https://graph.facebook.com/v8.0")
        # noinspection HardcodedPassword
        self.token = f"{config.FACEBOOK_APP_ID}|{config.FACEBOOK_APP_SECRET}"

    def _request(self, method, *args, **kwargs):
        response = self.cli.request(method, *args, **kwargs)
        response.raise_for_status()
        return response.json()

    def search_logs(self, query: str):
        return self._request(
            "GET",
            "/certificates",
            params={
                "access_token": self.token,
                "query": query,
                "fields": "domains,issuer_name",
            },
        )["data"]

    def subscribe(self, domain: str):
        return self._request(
            "POST",
            f"/{config.FACEBOOK_APP_ID}/subscribed_domains",
            data={
                "subscribe": domain,
                "access_token": self.token,
            },
        )

    def get_subscribed(self):
        return self._request(
            "GET",
            f"/{config.FACEBOOK_APP_ID}/subscribed_domains",
            params={
                "access_token": self.token,
                "fields": "domain",
            },
        )["data"]
