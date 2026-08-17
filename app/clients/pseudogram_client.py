from dataclasses import dataclass
from typing import Any

import httpx

from app.config.settings import get_settings


class PseudoGramError(Exception):
    """Base exception for PseudoGram API errors."""


class PseudoGramBadRequestError(PseudoGramError):
    """Raised when PseudoGram rejects a malformed request."""


class PseudoGramRateLimitError(PseudoGramError):
    """Raised when PseudoGram rate-limits our application."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(
            f"PseudoGram rate limit exceeded. Retry after {retry_after} seconds."
        )


class PseudoGramServerError(PseudoGramError):
    """Raised when PseudoGram returns a temporary server error."""


class PseudoGramUnexpectedError(PseudoGramError):
    """Raised for unexpected PseudoGram responses."""


@dataclass
class SendDMResult:
    """Result returned by PseudoGram after accepting a DM."""

    dm_id: str
    status: str


@dataclass
class DMStatusResult:
    """Current delivery status of a PseudoGram DM."""

    dm_id: str
    status: str
    recipient_user_id: str | None = None
    updated_at: str | None = None


class PseudoGramClient:
    """
    HTTP client for communicating with the PseudoGram mock API.
    """

    def __init__(self) -> None:
        settings = get_settings()

        self.base_url = settings.pseudogram_base_url.rstrip("/")
        self.api_key = settings.pseudogram_api_key

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=10.0,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self.client.aclose()

    async def send_dm(
        self,
        *,
        recipient_user_id: str,
        message: str,
        comment_id: str,
        idempotency_key: str,
    ) -> SendDMResult:
        """
        Send a DM through PseudoGram.

        The actual Mock API has been observed returning HTTP 200
        with status='queued'. The assignment documentation also
        describes HTTP 202 as an accepted response, so both are
        handled here.
        """

        response = await self.client.post(
            "/v1/dm/send",
            json={
                "recipient_user_id": recipient_user_id,
                "message": message,
                "comment_id": comment_id,
            },
            headers={
                "Idempotency-Key": idempotency_key,
            },
        )

        if response.status_code in (200, 202):
            data = response.json()

            return SendDMResult(
                dm_id=data["dm_id"],
                status=data["status"],
            )

        if response.status_code == 400:
            data = self._safe_json(response)

            detail = data.get(
                "detail",
                "PseudoGram rejected the request.",
            )

            raise PseudoGramBadRequestError(detail)

        if response.status_code == 429:
            retry_after = self._get_retry_after(response)

            raise PseudoGramRateLimitError(
                retry_after=retry_after,
            )

        if response.status_code == 500:
            raise PseudoGramServerError(
                "PseudoGram returned a temporary server error."
            )

        raise PseudoGramUnexpectedError(
            f"Unexpected PseudoGram response: {response.status_code}"
        )

    async def get_dm_status(
        self,
        dm_id: str,
    ) -> DMStatusResult:
        """
        Retrieve the current delivery status of a DM.
        """

        response = await self.client.get(
            f"/v1/dm/{dm_id}",
        )

        if response.status_code == 200:
            data = response.json()

            return DMStatusResult(
                dm_id=data["dm_id"],
                status=data["status"],
                recipient_user_id=data.get("recipient_user_id"),
                updated_at=data.get("updated_at"),
            )

        if response.status_code == 404:
            raise PseudoGramUnexpectedError(
                f"DM {dm_id} was not found."
            )

        if response.status_code >= 500:
            raise PseudoGramServerError(
                "PseudoGram returned a temporary server error."
            )

        raise PseudoGramUnexpectedError(
            f"Unexpected PseudoGram response: {response.status_code}"
        )

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        """Safely parse a JSON response."""

        try:
            data = response.json()

            if isinstance(data, dict):
                return data

        except ValueError:
            pass

        return {}

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> int:
        """Read and validate Retry-After."""

        value = response.headers.get("Retry-After")

        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            return 1