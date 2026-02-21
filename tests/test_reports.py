"""Unit tests for reports module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.models import HabitBase, HabitCompletion
from src.infrastructure.pdf.reports_service import ReportService, WeeklyReport

# HABITS_REPORT_LIST = [
#     {
#         "name": "Drink Water",
#         "total": 5,
#         "days": ["Mon", "Tue", "Wed"],
#         "status": "Active",
#     },
#     {"name": "Exercise", "total": 3, "days": ["Mon", "Wed"], "status": "Missed"},
#     {"name": "Read Book", "total": 0, "days": [], "status": "Missed"},
# ]


HABIT_REPORT = WeeklyReport(
    user_id=uuid4(),
    start_date=datetime(2026, 1, 26, 0, 0, 0),
    end_date=datetime(2026, 2, 1, 23, 59, 59),
    week_number=4,
    habits=[
        {
            "name": "Drink Water",
            "total": 5,
            "days": ["Mon", "Tue", "Wed"],
            "status": "Active",
        },
        {"name": "Exercise", "total": 3, "days": ["Mon", "Wed"], "status": "Missed"},
        {"name": "Read Book", "total": 0, "days": [], "status": "Missed"},
    ],
)


@pytest.mark.asyncio
async def test_calculate_weekly_stats_5_total_habit_completions(
    async_test_habits: list[HabitBase], mocked_habit_repository: AsyncMock
) -> None:
    """
    Test the calculation of weekly stats for a user.
    All habits are marked as done. There are 5 habits in total.
    """
    user_id = async_test_habits[0].user_id
    mock_active_habits = async_test_habits
    mock_repo = mocked_habit_repository
    mock_repo.get_all_habits_for_user.return_value = async_test_habits
    now = datetime.now(UTC)
    mock_completions = [HabitCompletion(id=uuid4(), habit_id=habit.id, completed_at=now) for habit in async_test_habits]
    mock_repo.get_completions_for_period.return_value = mock_completions
    report_gen = ReportService(mock_repo)
    report = await report_gen.calculate_weekly_stats(user_id=user_id)
    print(f"REPORT: {report}")
    assert report is not None
    assert len(report.habits) == len(mock_active_habits)


@pytest.mark.asyncio
async def test_calculate_weekly_stats_0_habit_completions(
    async_test_habits: list[HabitBase], mocked_habit_repository: AsyncMock
) -> None:
    """
    Test the calculation of weekly stats for a user.
    No habits are marked as done. There are 5 habits in total.
    """
    user_id = async_test_habits[0].user_id
    mock_active_habits = async_test_habits
    mock_repo = mocked_habit_repository
    mock_repo.get_all_habits_for_user.return_value = async_test_habits
    report_gen = ReportService(mock_repo)
    report = await report_gen.calculate_weekly_stats(user_id=user_id)
    assert report is not None
    assert len(report.habits) == len(mock_active_habits)


@pytest.mark.asyncio
async def test_calculate_weekly_stats_no_habits(mocked_habit_repository: AsyncMock) -> None:
    """
    Test the calculation of weekly stats for a user with no habits.
    """
    from uuid import UUID

    user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    report_gen = ReportService(mocked_habit_repository)
    report = await report_gen.calculate_weekly_stats(user_id=user_id)
    assert report is None


def test_render_html_report(mocked_habit_repository: AsyncMock) -> None:
    """Checks if habit report list is correctly rendered to a string"""
    report_gen = ReportService(mocked_habit_repository)
    start_date = datetime(2026, 1, 26, 0, 0, 0)
    end_date = datetime(2026, 2, 1, 23, 59, 59)
    rendered_report = report_gen.render_html_report(HABIT_REPORT)
    assert "Weekly Habit Report" in rendered_report
    assert f"Range: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}" in rendered_report
    for habit in HABIT_REPORT.habits:
        assert habit.name in rendered_report
        assert str(habit.total) in rendered_report
        assert habit.status in rendered_report
