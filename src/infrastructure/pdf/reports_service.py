"""Stats report generating functionalities"""

import os
import typing
from datetime import datetime, time, timedelta
from itertools import groupby
from typing import Any
from uuid import UUID

import jinja2
from jinja2.exceptions import TemplateError
from pydantic import BaseModel

from config import settings
from src.core.models import HabitBase
from src.repository.habit_repository import HabitRepository
from src.utils.logger import setup_logger

DB_URL = settings.DATABASE_URL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "data/templates")
DEFAULT_HTML_TEMPLATE = "weekly_report.html"
logger = setup_logger(__name__)


class HabitStats(BaseModel):
    """Stats for a single habit within a reporting period."""

    name: str
    total: int
    days: list[str]
    status: str


class WeeklyReport(BaseModel):
    """Complete weekly report with metadata + per-habit stats."""

    user_id: UUID
    start_date: datetime
    end_date: datetime
    week_number: int
    habits: list[HabitStats]

    @property
    def period_label(self) -> str:
        """Human-readable period string, e.g. '2026-02-02 – 2026-02-08'."""
        fmt = "%Y-%m-%d"
        return f"{self.start_date.strftime(fmt)} - {self.end_date.strftime(fmt)}"


class ReportService:
    """Generates reports based on the user request"""

    def __init__(self, habit_repo: HabitRepository) -> None:
        self.habit_repo = habit_repo

    def get_week_start_end_dates(self, current_date: datetime) -> tuple[datetime, datetime]:
        """
        Returns the start (Monday 00:00) and end (Sunday 23:59) of the week.
        """
        start_of_week = current_date - timedelta(days=current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        start_normalized = datetime.combine(start_of_week.date(), time.min)
        end_normalized = datetime.combine(end_of_week.date(), time.max)
        return start_normalized, end_normalized

    def create_report(
        self,
        active_habits: list[HabitBase],
        completed_habits: list[Any],
    ) -> list[HabitStats]:
        """Creates report of habits based on active and completed habits"""
        report = []
        completions_sorted = sorted(completed_habits, key=lambda x: x.habit_id)
        logs_by_habit_id = {
            habit_id: list(group) for habit_id, group in groupby(completions_sorted, key=lambda x: x.habit_id)
        }
        for habit in active_habits:
            habit_logs = logs_by_habit_id.get(habit.id, [])
            stats = HabitStats(
                name=habit.name,
                total=len(habit_logs),
                days=sorted({log.completed_at.strftime("%a") for log in habit_logs}),
                status="Missed" if not habit_logs else "Active",
            )
            report.append(stats)
        return report

    async def calculate_weekly_stats(self, user_id: UUID) -> WeeklyReport | None:
        """
        Calculates weekly habits stats for a user

        :user_id: ID of the user for whom the report is generated
        :return: WeeklyReport object with the calculated stats or None if there was
        an error during the calculation
        """
        if not user_id:
            logger.error(f"Error: no user_id provided: {user_id}")
            return None
        start, end = self.get_week_start_end_dates(datetime.now())
        if not start or not end:
            logger.error("Error: week start and week end not provided.")
            return None
        user_habits = await self.habit_repo.get_all_habits_for_user(user_id)
        if not user_habits:
            logger.info(f"No habits found for user {user_id}. Skipping report.")
            return None
        completed_habits = await self.habit_repo.get_completions_for_period(
            entity_id=user_id, start_date=start, end_date=end
        )
        habits = self.create_report(user_habits, completed_habits)
        weekly_report = WeeklyReport(
            user_id=user_id,
            start_date=start,
            end_date=end,
            week_number=datetime.now().isocalendar()[1],
            habits=habits,
        )
        if not weekly_report.habits or not weekly_report.week_number:
            logger.error(f"Error: no habits or week number found for user {user_id}.")
            return None
        return weekly_report

    def render_html_report(self, report: WeeklyReport) -> str:
        """
        Renders the weekly report to an HTML string using Jinja2 templates.

        :report: WeeklyReport object containing the report data
        :return: Rendered HTML report as string
        """
        try:
            template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
            template_env = jinja2.Environment(loader=template_loader)
            template = template_env.get_template(DEFAULT_HTML_TEMPLATE)
            html_output = template.render(
                habits=[h.model_dump() for h in report.habits],
                start_date=report.start_date,
                end_date=report.end_date,
            )
            return typing.cast(str, html_output)
        except TemplateError as e:
            logger.error(f"There was an error during rendering a templat: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error encountered during rendering a template: {e}")
            raise
