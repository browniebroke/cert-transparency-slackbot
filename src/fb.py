import httpx

from . import config


class Client:
    """API client for the facebook API."""

    def __init__(self):
        self.cli = httpx.Client(base_url="https://graph.facebook.com/v8.0")
        # noinspection HardcodedPassword
        self.token = f"{config.FACEBOOK_APP_ID}|{config.FACEBOOK_APP_SECRET}"

    def _request(self, method, *args, **kwargs):
        response = self.cli.request(method, *args, **kwargs)
        response.raise_for_status()
        return response.json()

    def search_logs(self, query: str):
        """Search the certificate transparency logs for the given query."""
        has_next = True
        params = {
            "access_token": self.token,
            "query": query,
            "fields": "domains,issuer_name",
        }
        while has_next:
            response_body = self._request("GET", "/certificates", params=params)
            yield from response_body["data"]
            has_next = "next" in response_body.get("paging", {})
            params["after"] = (
                response_body.get("paging", {}).get("cursors", {}).get("after", "")
            )

    def subscribe(self, domain: str):
        """Subscribe a new domain."""
        return self._request(
            "POST",
            f"/{config.FACEBOOK_APP_ID}/subscribed_domains",
            data={
                "subscribe": domain,
                "access_token": self.token,
            },
        )

    def get_subscribed(self):
        """List all subscribed domains."""
        return self._request(
            "GET",
            f"/{config.FACEBOOK_APP_ID}/subscribed_domains",
            params={
                "access_token": self.token,
                "fields": "domain",
            },
        )["data"]
