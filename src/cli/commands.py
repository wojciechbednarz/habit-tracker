"""CLI commands for Habit Tracker application."""

import click

from src.core.db import HabitDatabase
from src.core.greet import greet
from src.core.habit import HabitManager, UserBase, UserManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

__all__ = ["UserBase", "cli"]


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    "Habit Tracker - Track your daily habits -"
    "main CLI function to interact with the user"
    ctx.ensure_object(dict)
    click.echo("Welcome to Habit Tracker!")
    user_name = input("User name: ").strip()
    db = HabitDatabase()
    ctx.obj["tracker"] = HabitManager()
    user_manager = UserManager()
    with db.sync_session_maker() as session:
        user = session.query(UserBase).filter_by(user_name=user_name).first()
        if not user:
            email_address = input("Email address: ").strip()
            nickname = input("Nickname: ").strip()
            user = user_manager.create_user(
                user_name=user_name, email_address=email_address, nickname=nickname
            )
    ctx.obj["user_id"] = user.user_id


@cli.command()
@click.pass_context
def interactive(ctx: click.Context) -> None:
    """Start interactive mode"""
    tracker = ctx.obj["tracker"]
    click.echo("\nHabit Tracker - Interactive Mode")
    while tracker.running:
        click.echo("\nCommands: add | complete | list | quit")
        command = input("→ ").strip().lower()

        if command == "add":
            habit_name = input("Habit name: ").strip()
            habit_description = input("Habit description: ").strip()
            habit_frequency = input("Habit frequency: ").strip()
            click.echo(
                tracker.add_habit(
                    habit_name, habit_description, habit_frequency, ctx.obj["user_id"]
                )
            )

        elif command == "complete":
            habit_name = input("Habit name: ").strip()
            click.echo(tracker.complete_habit(habit_name, ctx.obj["user_id"]))

        elif command == "list":
            click.echo("\n")
            click.echo(tracker.list_habits(ctx.obj["user_id"]))

        elif command == "quit":
            click.echo("Goodbye! 👋")
            tracker.running = False

        else:
            click.echo("Unknown command")


@cli.command()
@click.option("--name", prompt=True, help="Habit name")
@click.option("--description", prompt=True, help="Habit description")
@click.option("--frequency", prompt=True, help="Habit frequency")
@click.pass_context
def add(
    ctx: click.Context, habit_name: str, habit_description: str, habit_frequency: str
) -> None:
    """Add a new habit"""
    tracker = ctx.obj["tracker"]
    user_id = ctx.obj["user_id"]
    click.echo(
        tracker.add_habit(habit_name, habit_description, habit_frequency, user_id)
    )
    click.echo("Habit added.")


@cli.command()
@click.argument("habit_name")
@click.pass_context
def complete(ctx: click.Context, habit_name: str) -> None:
    """Mark a habit as complete"""
    tracker = ctx.obj["tracker"]
    user_id = ctx.obj["user_id"]
    click.echo(tracker.complete_habit(habit_name, user_id))


@cli.command()
@click.pass_context
def list_all(ctx: click.Context) -> None:
    """List all habits"""
    tracker = ctx.obj["tracker"]
    user_id = ctx.obj["user_id"]
    click.echo(tracker.list_habits(user_id))


cli.add_command(greet)
