"""Core greeting functionality."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

import click

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass(frozen=True)
class TimestampFactory:
    """Timestamp factory, injects a clock for testability.
    Default: datetime.now(timezone.utc)"""

    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def __call__(self) -> datetime:
        """Allow instance() to return a fresh timestamp."""
        dt = self.clock()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt


class Greet:
    """Greet class to manage greeting state."""

    def __init__(self) -> None:
        """Greet class to manage greeting state."""
        self.timestamp_factory = TimestampFactory()
        self.last_greeted: datetime | None = None

    def last_time_greeted(self) -> str:
        """Return a string representation of the last greeted time."""
        logger.info(f"Last time you was greeted: {self.last_greeted}")
        if self.last_greeted is None:
            return "You have not been greeted yet."
        return f"Last time you was greeted: {self.last_greeted}"


greet_instance = Greet()


@click.command()
@click.option("--name", prompt="Your name", help="The person to greet")
@click.option("--prefix", prompt="Your prefix", help="Mr/Mrs/Ms")
@click.option("--number", default=1, help="Number of greetings")
def greet(
    prefix: str,
    name: Annotated[str, "Name of the person"],
    number: Annotated[int, "Number of greetings"],
) -> None:
    """Performs greeting using 'name' for a total of 'number' times."""
    try:
        logger.info(f"Greetings {number} times:")
        for _ in range(number):
            click.echo(f"Hello {prefix} {name}!")
        greet_instance.last_greeted = greet_instance.timestamp_factory()
        click.echo(greet_instance.last_time_greeted())
    except ValueError as err:
        raise click.BadParameter(f"Wrong parameter provided: {err}") from err


if __name__ == "__main__":
    greet()
