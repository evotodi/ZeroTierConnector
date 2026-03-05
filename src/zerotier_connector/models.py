from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from ipaddress import ip_address
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ZeroTierAccount(BaseModel):
    network_name: str
    network_id: str
    api_token: str
    ssh_username: str
    ssh_password: str | None = None
    ssh_key_path: str | None = None
    ssh_port: int = 22

    @field_validator("ssh_key_path")
    @classmethod
    def ExpandKeyPath(cls, value: str | None) -> str | None:
        if not value:
            return value
        return str(Path(value).expanduser())

    @model_validator(mode="after")
    def ValidateAuth(self) -> "ZeroTierAccount":
        if not self.ssh_password and not self.ssh_key_path:
            raise ValueError("At least one of ssh_password or ssh_key_path must be set.")
        return self

    @classmethod
    def Template(cls) -> "ZeroTierAccount":
        return cls(
            network_name="example-network",
            network_id="0123456789abcdef",
            api_token="replace-with-token",
            ssh_username="ubuntu",
            ssh_password="",
            ssh_key_path="~/.ssh/id_ed25519",
            ssh_port=22,
        )


class AppConfig(BaseModel):
    zerotier_uri: str = "https://api.zerotier.com/api/v1"
    member_freshness_minutes: int = 20
    cache_ttl_minutes: int = 60
    accounts: list[ZeroTierAccount] = Field(default_factory=list)

    @classmethod
    def Template(cls) -> "AppConfig":
        return cls(accounts=[ZeroTierAccount.Template()])


@dataclass(slots=True)
class NetworkMember:
    node_id: str
    name: str
    description: str
    authorized: bool
    last_seen: datetime | None
    ip_assignments: list[str]

    @property
    def DisplayName(self) -> str:
        memberName = NormalizeInlineText(self.name)
        memberDescription = NormalizeInlineText(self.description)
        if memberName and memberDescription and memberName != memberDescription:
            return f"{memberName} / {memberDescription}"
        return memberName or memberDescription or self.node_id

    @property
    def FirstIpv4(self) -> str | None:
        for candidateIp in self.ip_assignments:
            try:
                parsedIp = ip_address(candidateIp)
            except ValueError:
                continue
            if parsedIp.version == 4:
                return candidateIp
        return None

    def IsRecent(self, now: datetime, freshnessMinutes: int) -> bool:
        if self.last_seen is None:
            return False
        ageSeconds = (now - self.last_seen).total_seconds()
        return ageSeconds <= freshnessMinutes * 60

    @classmethod
    def FromApi(cls, payload: dict[str, Any]) -> "NetworkMember":
        configData = payload.get("config") or {}
        return cls(
            node_id=str(payload.get("nodeId", "")).strip(),
            name=str(payload.get("name", "")).strip(),
            description=str(payload.get("description", "")).strip(),
            authorized=bool(configData.get("authorized", False)),
            last_seen=ParseLastSeen(payload.get("lastSeen")),
            ip_assignments=list(configData.get("ipAssignments") or []),
        )


def ParseLastSeen(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, int):
        if value > 1_000_000_000_000:
            return datetime.fromtimestamp(value / 1000, tz=UTC)
        return datetime.fromtimestamp(value, tz=UTC)

    if isinstance(value, float):
        return datetime.fromtimestamp(value, tz=UTC)

    if isinstance(value, str):
        strippedValue = value.strip()
        if strippedValue.isdigit():
            return ParseLastSeen(int(strippedValue))
        try:
            return datetime.fromisoformat(strippedValue.replace("Z", "+00:00")).astimezone(
                UTC
            )
        except ValueError:
            return None
    return None


def NormalizeInlineText(value: str) -> str:
    return " ".join(value.split())
