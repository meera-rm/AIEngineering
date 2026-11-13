"""HTTP clients for the routing and retrieval containers (Homework 7)."""

import requests

DEFAULT_TIMEOUT_S = 60


class RetrievalUnavailableError(Exception):
    """Retrieval is unreachable, timed out, or returned 503; the workflow may retry."""


class ServiceCallError(Exception):
    """A routing or retrieval call failed in a way that is not retried."""


class RoutingClient:
    """Calls the router container's POST /route."""

    def __init__(self, base_url: str, timeout_s: float = DEFAULT_TIMEOUT_S):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def route_ticket(self, request: dict) -> dict:
        try:
            response = requests.post(f"{self.base_url}/route", json=request, timeout=self.timeout_s)
        except requests.RequestException as e:
            raise ServiceCallError("routing service unreachable") from e
        if response.status_code != 200:
            raise ServiceCallError(f"routing service returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as e:
            raise ServiceCallError("routing response was not JSON") from e


class RetrievalClient:
    """Calls the retrieval container's POST /search."""

    def __init__(self, base_url: str, timeout_s: float = DEFAULT_TIMEOUT_S):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def retrieve_evidence(self, request: dict) -> dict:
        try:
            response = requests.post(f"{self.base_url}/search", json=request, timeout=self.timeout_s)
        except (requests.ConnectionError, requests.Timeout) as e:
            raise RetrievalUnavailableError("retrieval service unreachable") from e
        except requests.RequestException as e:
            raise ServiceCallError("retrieval request failed") from e
        if response.status_code == 503:
            raise RetrievalUnavailableError("retrieval service temporarily unavailable")
        if response.status_code != 200:
            raise ServiceCallError(f"retrieval service returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as e:
            raise ServiceCallError("retrieval response was not JSON") from e
