# Habit Tracker

A command-line application for tracking daily habits with SQLite persistence.

## Features

- Add and manage habits with custom descriptions and frequencies
- Mark habits as complete
- Track habit completion status
- Per-user habit tracking
- Interactive and command-line modes
- SQLite database for persistent storage

## Requirements

- Python 3.8+
- click
- pytest

## Installation

```bash
git clone https://github.com/wojciechbednarz/habit-tracker.git
cd habit-tracker
pip install -e .
```

## Usage

### Interactive Mode

```bash
python -m src.main interactive
```

Available commands in interactive mode:
- `add` - Add a new habit with name, description, and frequency
- `complete` - Mark a habit as complete
- `list` - Display all habits
- `data` - Display habit data
- `quit` - Exit interactive mode

### Command-Line Mode

```bash
# Add a habit
python -m src.main add "Morning Exercise"

# Mark a habit as complete
python -m src.main complete "Morning Exercise"

# List all habits
python -m src.main list-all

# Specify user (default: "default")
python -m src.main --user john interactive
```

### Additional Commands

```bash
# Greeting command
python -m src.main greet --name John --prefix Mr --number 3
```

```bash
# Running the file from root
python -m src.core.habit
```

## Project Structure

```
habit-tracker/
├── src/
│   ├── cli/
│   │   └── commands.py      # Click CLI commands
│   ├── core/
│   │   ├── db/
│   │   │   └── crud.py      # Database operations
│   │   ├── greet.py         # Greeting functionality
│   │   └── habit.py         # Core habit logic
│   ├── utils/
│   │   ├── helpers.py       # Utility functions
│   │   └── logger.py        # Logging configuration
│   └── main.py              # Application entry point
├── tests/
│   └── test_habit_handler.py
├── conftest.py
└── pyproject.toml
```

## Development

### Running Tests

```bash
pytest
```

### Database

The application uses SQLite database (`habit_tracker.db`) stored in the project root. The database is created automatically on first run.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Author

Wojciech Bednarz

Project Link: [https://github.com/wojciechbednarz/habit-tracker](https://github.com/wojciechbednarz/habit-tracker)