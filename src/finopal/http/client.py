"""Thin HTTP client shared by every resource.

Responsibilities:

* build the absolute URL from :class:`~finopal.utils.config.Config`;
* inject ``merchant_id`` (callers may override it per call);
* send the standard FinoPal headers;
* guarantee a ``dict`` comes back, or raise :class:`TransportError`.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from finopal.errors.exceptions import TransportError
from finopal.http.transport import Transport
from finopal.utils.config import Config

__all__ = ["HttpClient"]


class HttpClient:
    """Wraps a :class:`Transport` with FinoPal-specific request shaping."""

    def __init__(self, config: Config, transport: Transport) -> None:
        self.config = config
        self.transport = transport

    @property
    def base_url(self) -> str:
        return self.config.base_url

    def headers(self, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }
        headers.update(dict(extra or {}))
        return headers

    def post(
        self,
        path: str,
        payload: Optional[Mapping[str, Any]] = None,
        *,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        """POST ``payload`` to ``path`` with ``merchant_id`` injected.

        A ``merchant_id`` present in ``payload`` wins, so a single client can
        serve several terminals when needed.
        """
        url = self.config.endpoint(path)
        body: Dict[str, Any] = {"merchant_id": self.config.merchant_id}
        body.update(dict(payload or {}))

        response = self.transport.post_json(url, body, self.headers(headers))

        if not isinstance(response, Mapping):
            raise TransportError(
                "Malformed response from {}: expected a JSON object.".format(url)
            )
        return dict(response)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "HttpClient(base_url={!r}, transport={})".format(
            self.base_url, type(self.transport).__name__
        )
