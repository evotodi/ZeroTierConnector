from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .config import VarDir
from .models import NetworkMember


class MemberCache:
    def __init__(self, baseDir: Path | None = None) -> None:
        self.baseDir = baseDir or VarDir()
        self.baseDir.mkdir(parents=True, exist_ok=True)

    def Read(self, networkId: str, ttlMinutes: int) -> list[NetworkMember] | None:
        cachePath = self.CacheFile(networkId)
        if not cachePath.exists():
            return None

        modifiedAt = datetime.fromtimestamp(cachePath.stat().st_mtime, tz=UTC)
        expiresAt = modifiedAt + timedelta(minutes=ttlMinutes)
        if expiresAt < datetime.now(tz=UTC):
            return None

        rawMembers = json.loads(cachePath.read_text(encoding="utf-8"))
        members: list[NetworkMember] = []
        for memberData in rawMembers:
            memberData = dict(memberData)
            if memberData.get("last_seen"):
                memberData["last_seen"] = datetime.fromisoformat(memberData["last_seen"])
            members.append(NetworkMember(**memberData))
        return members

    def Write(self, networkId: str, members: list[NetworkMember]) -> None:
        serializedMembers = []
        for member in members:
            memberData = asdict(member)
            if member.last_seen is not None:
                memberData["last_seen"] = member.last_seen.isoformat()
            serializedMembers.append(memberData)
        self.CacheFile(networkId).write_text(
            json.dumps(serializedMembers, indent=2), encoding="utf-8"
        )

    def CacheFile(self, networkId: str) -> Path:
        return self.baseDir / f"members_{networkId}.json"
