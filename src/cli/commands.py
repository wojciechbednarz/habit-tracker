# click commands for setting up habits
from src.utils.logger import setup_logger
from src.core.habit import HabitCore
from src.core.greet import greet
import click


logger = setup_logger(__name__)


@click.group()
@click.option("--user", default="default", help="User indentifier")
@click.pass_context
def cli(ctx, user) -> None:
    "Habit Tracker - Track your daily habits - main CLI function to interact with the user"
    ctx.ensure_object(dict)
    click.echo("Welcome to Habit Tracker!")
    click.echo(f"User: {user}\n")
    ctx.obj["tracker"] = HabitCore(user_data=user)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode"""
    tracker = ctx.obj["tracker"]
    click.echo(f"\nHabit Tracker - Interactive Mode")
    while tracker.running:
        click.echo("\nCommands: add | complete | list | data | quit")
        command = input("→ ").strip().lower()

        if command == "add":
            habit_name = input("Habit name: ").strip()
            habit_description = input("Habit description: ").strip()
            habit_frequency = input("Habit frequency: ").strip()
            click.echo(
                tracker.add_habit(habit_name, habit_description, habit_frequency)
            )

        elif command == "complete":
            habit_name = input("Habit name: ").strip()
            click.echo(tracker.complete_habit(habit_name))

        elif command == "list":
            click.echo("\n")
            click.echo(tracker.list_habits())

        elif command == "data":
            click.echo(tracker.display_data())

        elif command == "quit":
            click.echo("Goodbye! 👋")
            tracker.running = False

        else:
            click.echo("Unknown command")


@cli.command()
@click.argument("habit_name")
@click.pass_context
def add(ctx, habit_name):
    """Add a new habit"""
    tracker = ctx.obj["tracker"]
    click.echo(tracker.add_habit(habit_name))


@cli.command()
@click.argument("habit_name")
@click.pass_context
def complete(ctx, habit_name):
    """Mark a habit as complete"""
    tracker = ctx.obj["tracker"]
    click.echo(tracker.mark_done(habit_name))


@cli.command()
@click.pass_context
def list_all(ctx):
    """List all habits"""
    tracker = ctx.obj["tracker"]
    click.echo(tracker.list_habits())


cli.add_command(greet)
