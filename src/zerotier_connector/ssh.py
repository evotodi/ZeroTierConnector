from __future__ import annotations

import shutil
import subprocess

from .models import ZeroTierAccount


class SSHConnector:
    def __init__(self):
        self.sshDefaultOptions = [
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
        ]

    def Connect(self, account: ZeroTierAccount, ip: str) -> int:
        if account.ssh_key_path:
            sshCommand = [
                "ssh",
                "-i",
                account.ssh_key_path,
            ]

            sshCommand.extend(self.sshDefaultOptions)
            sshCommand.extend([
                "-p",
                str(account.ssh_port),
                f"{account.ssh_username}@{ip}",
            ])

            return subprocess.call(sshCommand)

        if account.ssh_password:
            # noinspection deprecation
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
            ]

            sshCommand.extend(self.sshDefaultOptions)
            sshCommand.extend([
                "-p",
                str(account.ssh_port),
                f"{account.ssh_username}@{ip}",
            ])

            return subprocess.call(sshCommand)

        raise RuntimeError("No SSH authentication method configured.")
