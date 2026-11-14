from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from playwright.sync_api import APIRequestContext, APIResponse

LOGGER = logging.getLogger("checkout-api")


@dataclass
class PaymentCall:
    method: str
    url: str
    params: dict
    http_status: int
    body: dict | str
    headers: dict

    def as_log(self) -> str:
        body = (
            json.dumps(self.body, indent=2, ensure_ascii=False)
            if isinstance(self.body, (dict, list))
            else self.body
        )
        return (
            f"{self.method} {self.url}\n"
            f"Query: {self.params}\n"
            f"HTTP {self.http_status}\n"
            f"Headers: {self.headers}\n"
            f"Body:\n{body}"
        )


class PaymentApi:
    def __init__(self, request_context: APIRequestContext, base_url: str):
        self._request = request_context
        self._base_url = base_url.rstrip("/")
        self.last_call: PaymentCall | None = None

    def get_payment_methods(self, cell_number: str) -> tuple[int, dict | str]:
        url = f"{self._base_url}/payment/"
        params = {"CellNumber": cell_number}
        LOGGER.info("REQUEST GET %s params=%s", url, params)
        response: APIResponse = self._request.get(url, params=params)
        body = self._parse_body(response)
        self.last_call = PaymentCall(
            method="GET",
            url=response.url,
            params=params,
            http_status=response.status,
            body=body,
            headers=dict(response.headers),
        )
        LOGGER.info("RESPONSE HTTP %s\n%s", response.status, self.last_call.as_log())
        return response.status, body

    @staticmethod
    def _parse_body(response: APIResponse) -> dict | str:
        try:
            return response.json()
        except Exception:
            return response.text()
