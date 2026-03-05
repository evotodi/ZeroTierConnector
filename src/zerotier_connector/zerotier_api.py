from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urljoin

import requests

from .models import NetworkMember, ZeroTierAccount


class ZeroTierClient:
    def __init__(self, baseUri: str) -> None:
        self.baseUri = baseUri.rstrip("/") + "/"

    def ListMembers(self, account: ZeroTierAccount) -> list[NetworkMember]:
        endpoint = urljoin(self.baseUri, f"network/{account.network_id}/member")
        response = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {account.api_token}"},
            timeout=20,
        )
        response.raise_for_status()
        payloadData = response.json()
        if not isinstance(payloadData, list):
            raise ValueError("Unexpected API response. Expected a list of members.")
        return [NetworkMember.FromApi(item) for item in payloadData]

    @staticmethod
    def FilterAuthorizedRecent(
        members: list[NetworkMember], freshnessMinutes: int
    ) -> list[NetworkMember]:
        now = datetime.now(tz=UTC)
        return [
            member
            for member in members
            if member.authorized and member.IsRecent(now, freshnessMinutes)
        ]
