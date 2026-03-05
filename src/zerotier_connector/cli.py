from __future__ import annotations

import click

from typing import Literal

from .cache import MemberCache
from .models import AppConfig, NetworkMember, ZeroTierAccount
from .ssh import SSHConnector
from .zerotier_api import ZeroTierClient


class App:
    def __init__(self, config: AppConfig, noColor: bool = False) -> None:
        self.configData = config
        self.noColor = noColor
        self.zeroTierClient = ZeroTierClient(config.zerotier_uri)
        self.memberCache = MemberCache()
        self.sshConnector = SSHConnector()

    def Run(self) -> int:
        self.ShowLogo()
        if not self.configData.accounts:
            click.echo("No accounts configured.")
            return 1

        selectedAccount = self.SelectAccount()
        if selectedAccount is None:
            return 0

        members = self.LoadMembers(selectedAccount, forceRefresh=False)
        if members is None:
            return 1

        while True:
            selectedAction = self.SelectMemberOrAction(members)
            if selectedAction == "q":
                return 0
            if selectedAction == "r":
                members = self.LoadMembers(selectedAccount, forceRefresh=True)
                if members is None:
                    return 1
                continue
            if selectedAction == "s":
                selectedMember = self.SearchAndSelectMember(members)
                if selectedMember == "quit":
                    return 0
                if selectedMember is None:
                    continue
                connectStatus = self.ConnectToMember(selectedAccount, selectedMember)
                if connectStatus is None:
                    continue
                return connectStatus

            selectedMember = members[int(selectedAction)]
            connectStatus = self.ConnectToMember(selectedAccount, selectedMember)
            if connectStatus is None:
                continue
            return connectStatus

    def SelectAccount(self) -> ZeroTierAccount | None:
        if len(self.configData.accounts) == 1:
            return self.configData.accounts[0]

        self.EchoHeading("Select a ZeroTier account:")
        for index, account in enumerate(self.configData.accounts, start=1):
            self.EchoSelectableItem(
                f"{index}", f"{account.network_name} ({account.network_id})"
            )
        click.echo("")
        self.EchoSelectableItem("q", "Quit")

        validChoices = [str(index) for index in range(1, len(self.configData.accounts) + 1)]
        validChoices.append("q")

        while True:
            choiceText = click.prompt(
                ">",
                type=click.Choice(validChoices, case_sensitive=False),
                show_choices=False,
            ).lower()
            if choiceText == "q":
                return None
            selectedIndex = int(choiceText) - 1
            return self.configData.accounts[selectedIndex]

    def LoadMembers(
            self, account: ZeroTierAccount, forceRefresh: bool
    ) -> list[NetworkMember] | None:
        members = None
        if not forceRefresh:
            cachedMembers = self.memberCache.Read(
                account.network_id, self.configData.cache_ttl_minutes
            )
            if cachedMembers is not None:
                members = self.zeroTierClient.FilterAuthorizedRecent(
                    cachedMembers, self.configData.member_freshness_minutes
                )
                click.echo(f"Using cached members ({len(members)}).")
                return members

        try:
            fetchedMembers = self.zeroTierClient.ListMembers(account)
        except Exception as exc:  # noqa: BLE001
            click.echo(f"Failed to fetch members: {exc}", err=True)
            return None

        filteredMembers = self.zeroTierClient.FilterAuthorizedRecent(
            fetchedMembers, self.configData.member_freshness_minutes
        )
        self.memberCache.Write(account.network_id, filteredMembers)
        click.echo(f"Fetched and cached members ({len(filteredMembers)}).")
        return filteredMembers

    def SelectMemberOrAction(self, members: list[NetworkMember]) -> str:
        self.EchoHeading("\nSelect member:")
        if members:
            for index, member in enumerate(members, start=1):
                self.EchoSelectableItem(f"{index}", member.DisplayName)
        else:
            click.echo("No authorized active members found.")
        click.echo("")
        self.EchoSelectableItem("s", "Search members")
        self.EchoSelectableItem("r", "Refresh members")
        self.EchoSelectableItem("q", "Quit")

        validChoices = [str(index) for index in range(1, len(members) + 1)]
        validChoices.extend(["s", "r", "q"])

        choiceText = click.prompt(
            ">",
            type=click.Choice(validChoices, case_sensitive=False),
            show_choices=False,
        ).lower()
        if choiceText in {"q", "r", "s"}:
            return choiceText
        return str(int(choiceText) - 1)

    def SearchAndSelectMember(
            self, members: list[NetworkMember]
    ) -> NetworkMember | None | Literal["quit"]:
        promptLabel = "Search text"
        if not self.noColor:
            promptLabel = click.style(promptLabel, fg="red")
        searchTerm = click.prompt(promptLabel, type=str).strip().lower()
        if not searchTerm:
            click.echo("Search text cannot be empty.")
            return None

        matchingMembers = [
            member
            for member in members
            if searchTerm in member.DisplayName.lower()
               or searchTerm in member.node_id.lower()
        ]
        if not matchingMembers:
            click.echo("No matching members found.")
            return None

        self.EchoHeading("\nSearch results:")
        for index, member in enumerate(matchingMembers, start=1):
            self.EchoSelectableItem(f"{index}", member.DisplayName)
        click.echo("")
        self.EchoSelectableItem("c", "Cancel")
        self.EchoSelectableItem("q", "Quit")

        validChoices = [str(index) for index in range(1, len(matchingMembers) + 1)]
        validChoices.extend(["c", "q"])
        choiceText = click.prompt(
            ">",
            type=click.Choice(validChoices, case_sensitive=False),
            show_choices=False,
        ).lower()
        if choiceText == "c":
            return None
        if choiceText == "q":
            return "quit"

        selectedIndex = int(choiceText) - 1
        return matchingMembers[selectedIndex]

    def ConnectToMember(
            self, account: ZeroTierAccount, selectedMember: NetworkMember
    ) -> int | None:
        selectedIp = selectedMember.FirstIpv4
        if not selectedIp:
            click.echo("Selected member has no IPv4 assignment.")
            return None

        click.echo(f"Connecting to {selectedMember.DisplayName} ({selectedIp})...")
        try:
            return self.sshConnector.Connect(account, selectedIp)
        except RuntimeError as exc:
            click.echo(f"SSH error: {exc}", err=True)
            return 2

    def EchoHeading(self, text: str) -> None:
        if self.noColor:
            click.echo(text)
            return
        click.echo(click.style(text, fg="green"))

    def EchoSelectableItem(self, selector: str, label: str) -> None:
        if self.noColor:
            click.echo(f"{selector}. {label}")
            return
        prefixText = click.style(f"{selector}.", fg="cyan")
        click.echo(f"{prefixText} {label}")

    def ShowLogo(self) -> None:
        logoText = r"""
 ______              _______                  _____                              _
|___  /             |__   __(_)              / ____|                            | |
   / /  ___ _ __ ___   | |   _  ___ _ __    | |       ___  _ __  _ __   ___  ___| |_ ___  _ __
  / /  / _ \ '__/ _ \  | |  | |/ _ \ '__|   | |      / _ \| '_ \| '_ \ / _ \/ __| __/ _ \| '__|
 / /__|  __/ | | (_) | | |  | |  __/ |      | |____ | (_) | | | | | | |  __/ (__| || (_) | |
/_____\___|_|  \___/   |_|  |_|\___|_|       \_____| \___/|_| |_|_| |_|\___|\___|\__\___/|_|
"""

        if self.noColor:
            click.echo(logoText)
        else:
            click.echo(click.style(logoText, fg="green"))


def RunApp(config: AppConfig, noColor: bool = False) -> int:
    app = App(config, noColor=noColor)
    return app.Run()


def MainFromConfig(config: AppConfig, noColor: bool = False) -> None:
    raise SystemExit(RunApp(config, noColor=noColor))
