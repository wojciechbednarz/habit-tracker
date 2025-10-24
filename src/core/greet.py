from typing_extensions import Annotated
from typing import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import sys
import os
# Add the project root to Python path to allow imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.utils.logger import setup_logger
import click



logger = setup_logger(__name__)


@dataclass(frozen=True)
class TimestampFactory:
    """Timestamp factory, injects a clock for testability.
    Default: datetime.now(timezone.utc)"""
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)

    def __call__(self) -> datetime:
        """Allow instance() to return a fresh timestamp."""
        dt = self.clock()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt

class Greet:
    def __init__(self):
        self.timestamp_factory = TimestampFactory()
        self.last_greeted = None

    def last_time_greeted(self):
        logger.info(f"Last time you was greeted: {self.last_greeted}")

greet_instance = Greet()


@click.command()
@click.option("--name", prompt="Your name", help="The person to greet")
@click.option("--prefix", prompt="Your prefix", help="Mr/Mrs/Ms")
@click.option("--number", default=1, help="Number of greetings")
def greet(prefix: str, name: Annotated[str, "Name of the person"],
        number: Annotated[int, "Number of greetings"]) -> None:
    """Performs greeting using 'name' for a total of 'number' times."""
    try:
        logger.info(f"Greetings {number} times:")
        for i in range(number):
            click.echo(f"Hello {prefix} {name}!")
        greet_instance.last_greeted = greet_instance.timestamp_factory()
        click.echo(greet_instance.last_time_greeted())
    except ValueError as err:
        raise click.BadParameter(f"Wrong parameter provided: {err}")


if __name__ == "__main__":
    greet()
    

    