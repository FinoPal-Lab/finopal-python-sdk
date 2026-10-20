"""Transport layer.

The SDK talks to the gateway through a tiny abstraction — :class:`Transport` —
so the HTTP implementation can be swapped without touching the resource
classes. This mirrors ``FinoPal\\Sdk\\Http\\TransportInterface`` in the PHP SDK
and makes the whole package testable without mocking ``requests``.

Built-in implementations:

* :class:`RequestsTransport` — default, backed by ``requests.Session``.
* :class:`CallableTransport` — wraps any ``fn(url, body, headers) -> dict``,
  which is what the test-suite and most integrations use for stubs.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Mapping, Optional

import requests

from finopal.errors.exceptions import TransportError

__all__ = ["Transport", "RequestsTransport", "CallableTransport"]


class Transport:
    """Interface every transport must implement."""

    def post_json(
        self,
        url: str,
        body: Mapping[str, Any],
        headers: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        """POST ``body`` as JSON to ``url`` and return the decoded response.

        :raises TransportError: on connection failure, timeout, non-JSON body
            or a 5xx response.
        """
        raise NotImplementedError


class RequestsTransport(Transport):
    """Default transport built on ``requests.Session``.

    A single session is reused so TCP connections and TLS handshakes are
    pooled across calls.

    :param timeout: Per-request timeout in seconds.
    :param verify: TLS verification. Keep ``True`` in production.
    :param max_retries: Extra attempts for connection errors only.
    :param session: Inject a pre-configured session (proxies, adapters...).
    """

    def __init__(
        self,
        timeout: float = 30.0,
        verify: bool = True,
        max_retries: int = 0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.timeout = float(timeout)
        self.verify = bool(verify)
        self.max_retries = max(0, int(max_retries))
        self.session = session or requests.Session()

    def post_json(
        self,
        url: str,
        body: Mapping[str, Any],
        headers: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        payload = dict(body)
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        request_headers.update(dict(headers or {}))

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    headers=request_headers,
                    timeout=self.timeout,
                    verify=self.verify,
                )
            except requests.RequestException as exc:
                last_error = exc
                # Only connection-level problems are worth retrying; the SDK
                # never retries a request the gateway may have already handled.
                if attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise TransportError(
                    "Could not reach the FinoPal gateway at {}: {}".format(url, exc)
                ) from exc

            return self._decode(response, url)

        raise TransportError(  # pragma: no cover - loop always raises or returns
            "Could not reach the FinoPal gateway at {}: {}".format(url, last_error)
        )

    @staticmethod
    def _decode(response: requests.Response, url: str) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            snippet = (response.text or "")[:300]
            raise TransportError(
                "The FinoPal gateway returned a non-JSON response "
                "(HTTP {}) from {}: {!r}".format(response.status_code, url, snippet),
                status_code=response.status_code,
            ) from exc

        if not isinstance(data, dict):
            raise TransportError(
                "Unexpected response shape from {} (expected a JSON object, "
                "got {}).".format(url, type(data).__name__),
                status_code=response.status_code,
            )

        # 5xx means the gateway itself failed — surface it as a transport error.
        # 4xx bodies are usually structured FinoPal errors, so let the resource
        # layer interpret them.
        if response.status_code >= 500:
            raise TransportError(
                "The FinoPal gateway returned HTTP {} from {}.".format(
                    response.status_code, url
                ),
                status_code=response.status_code,
                response=data,
            )

        return data


class CallableTransport(Transport):
    """Adapt a plain function into a transport.

    Handy in tests and in frameworks that already own an HTTP client::

        def fake(url, body, headers):
            return {"success": True, "code": 100,
                    "data": {"authority": "FP_1", "payment_url": "https://x"}}

        finopal = FinoPal(config, transport=CallableTransport(fake))
    """

    def __init__(
        self,
        handler: Callable[[str, Mapping[str, Any], Mapping[str, str]], Mapping[str, Any]],
    ) -> None:
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._handler = handler

    def post_json(
        self,
        url: str,
        body: Mapping[str, Any],
        headers: Optional[Mapping[str, str]] = None,
    ) -> Dict[str, Any]:
        result = self._handler(url, dict(body), dict(headers or {}))
        if not isinstance(result, Mapping):
            raise TransportError(
                "CallableTransport handler must return a mapping, got {}.".format(
                    type(result).__name__
                )
            )
        return dict(result)
