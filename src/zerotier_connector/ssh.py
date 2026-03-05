from __future__ import annotations

import shutil
import subprocess

from .models import ZeroTierAccount


class SSHConnector:
    def Connect(self, account: ZeroTierAccount, ip: str) -> int:
        if account.ssh_key_path:
            sshCommand = [
                "ssh",
                "-i",
                account.ssh_key_path,
                "-p",
                str(account.ssh_port),
                f"{account.ssh_username}@{ip}",
            ]
            return subprocess.call(sshCommand)

        if account.ssh_password:
            sshpassPath = shutil.which("sshpass")
            if not sshpassPath:
                raise RuntimeError(
                    "sshpass is required for password auth. Install it or configure ssh_key_path."
                )
            sshCommand = [
                sshpassPath,
                "-p",
                account.ssh_password,
                "ssh",
                "-p",
                str(account.ssh_port),
                f"{account.ssh_username}@{ip}",
            ]
            return subprocess.call(sshCommand)

        raise RuntimeError("No SSH authentication method configured.")
