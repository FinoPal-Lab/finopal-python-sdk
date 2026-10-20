"""Runtime configuration for the FinoPal SDK."""

from __future__ import annotations

from typing import Optional

__all__ = ["Config", "LIVE_BASE_URL", "SANDBOX_BASE_URL", "DEFAULT_USER_AGENT"]

#: Production (live) FinoPal gateway host.
LIVE_BASE_URL = "https://payment.finopal.ir"

#: Sandbox host. Same API surface as production, no real money moves.
SANDBOX_BASE_URL = "https://sandbox.finopal.ir"

DEFAULT_USER_AGENT = "FinoPalPythonSdk/0.1.0 (+https://finopal.ir/docs)"


class Config:
    """Configuration object handed to :class:`finopal.FinoPal`.

    :param merchant_id: The 24-character terminal identifier issued by FinoPal
        (looks like ``fino-xxxx-xxxx-xxxx-xxxx``). Required.
    :param sandbox: Route every call to the sandbox host instead of production.
    :param base_url: Explicit host override. Useful for a local mock gateway or
        a private staging deployment. Takes precedence over ``sandbox``.
    :param timeout: Per-request timeout in seconds.
    :param verify_ssl: Set to ``False`` only when talking to a self-signed
        staging host. Never disable this in production.
    :param max_retries: Number of additional attempts for *connection* errors
        (never for a request the gateway already answered).
    :param user_agent: Override the ``User-Agent`` header sent with every call.

    Example::

        from finopal import FinoPal, Config

        config = Config(merchant_id="fino-1234-5678-9012-3456", sandbox=True)
    """

    LIVE_BASE_URL = LIVE_BASE_URL
    SANDBOX_BASE_URL = SANDBOX_BASE_URL

    def __init__(
        self,
        merchant_id: str,
        sandbox: bool = False,
        *,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        max_retries: int = 0,
        user_agent: Optional[str] = None,
    ) -> None:
        if merchant_id is None or not str(merchant_id).strip():
            raise ValueError(
                "merchant_id is required. Copy the terminal id from your "
                "FinoPal panel (fino-xxxx-xxxx-xxxx-xxxx)."
            )

        self.merchant_id: str = str(merchant_id).strip()
        self.sandbox: bool = bool(sandbox)
        self.timeout: float = float(timeout)
        self.verify_ssl: bool = bool(verify_ssl)
        self.max_retries: int = max(0, int(max_retries))
        self.user_agent: str = user_agent or DEFAULT_USER_AGENT
        self._base_url: Optional[str] = base_url.rstrip("/") if base_url else None

    @property
    def base_url(self) -> str:
        """Effective gateway host, without a trailing slash."""
        if self._base_url:
            return self._base_url
        return self.SANDBOX_BASE_URL if self.sandbox else self.LIVE_BASE_URL

    def endpoint(self, path: str) -> str:
        """Join ``path`` onto :attr:`base_url`.

        >>> Config("fino-x").endpoint("/api/v1/payment/request")
        'https://payment.finopal.ir/api/v1/payment/request'
        """
        return "{}/{}".format(self.base_url.rstrip("/"), str(path).lstrip("/"))

    def __repr__(self) -> str:
        mode = "sandbox" if self.sandbox else "live"
        return "Config(merchant_id={!r}, mode={!r}, base_url={!r})".format(
            self.merchant_id, mode, self.base_url
        )
