from __future__ import annotations

import click
from pydantic import ValidationError

from .cli import MainFromConfig
from .config import ConfigLoader


@click.command()
@click.option(
    "--no-color",
    "noColor",
    is_flag=True,
    help="Disable colored menu output.",
)
def Main(noColor: bool) -> None:
    loader = ConfigLoader()
    try:
        config = loader.Load()
    except FileNotFoundError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1) from exc
    except ValidationError as exc:
        click.echo("Invalid config.json:", err=True)
        for error in exc.errors():
            path = ".".join(str(part) for part in error.get("loc", []))
            click.echo(f"- {path}: {error.get('msg')}", err=True)
        raise SystemExit(1) from exc
    MainFromConfig(config, noColor=noColor)


if __name__ == "__main__":
    Main()
