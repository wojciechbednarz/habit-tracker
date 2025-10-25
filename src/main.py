"""Main application entry point."""
from src.cli.commands import cli
from src.core.habit import HabitCore




def main():
    """Main entry point for the application."""
    cli()
    # habit_core = HabitCore()
    # habit_core.initialize_database()
    # habit_core.add_habit(name="Meditation", description="Meditate for 10 minutes every day", frequency="Daily")
    # habit_core.list_habits()
    # habit.add_habit(name="Playing chess daily", description="I want to play chess daily to reach 1000 ELO", frequency="Daily")
    # habit.add_habit(name="Reading books", description="Read at least one book per month", frequency="Monthly")
    # habit.add_habit(name="Morning Exercise", description="Do a 30-minute workout every morning", frequency="Daily")
    # habit.add_habit(name="Meditation", description="Meditate for 10 minutes every day", frequency="Daily")
    # habit.modify_habit(
    #     updated_habit={
    #         "name": "Playing chess weekly",
    #         "description": "I want to play chess weekly to reach 1000 ELO",
    #         "frequency": "Weekly"
    #     },
    #     value_to_update="Playing chess daily"
    # )
    # habit.list_habits()
    # habit.mark_done("Morning Exercise")


if __name__ == "__main__":
    main()