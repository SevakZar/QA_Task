from __future__ import annotations

import json
from dataclasses import dataclass

from playwright.sync_api import APIRequestContext, APIResponse


@dataclass
class PaymentCall: ## for handeling log
    ## Request information
    method: str
    url: str
    params: dict
    ## Response information
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
        self.last_call: PaymentCall | None = None ## This creates a variable to store the most recent API call.

    def get_payment_methods(self, cell_number: str) -> tuple[int, dict | str]: ## the method returns a tuple containing: int(HTTP status) & dict or str (response body)
        url = f"{self._base_url}/payment/"
        params = {"CellNumber": cell_number}
        response: APIResponse = self._request.get(url, params=params) ##1 enough for api call - response should be APIResponse type
        body = self._parse_body(response) ##2 enough for api call
        self.last_call = PaymentCall(
            method="GET",
            url=response.url,
            params=params,
            http_status=response.status,
            body=body,
            headers=dict(response.headers),
        )
        return response.status, body ##3 enough for api call

    @staticmethod
    def _parse_body(response: APIResponse) -> dict | str:
        try: ## Python's error-handling mechanism
            return response.json()
        except Exception:
            return response.text()
