from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.core.schemas import CoachContext, HabitResponse


def make_habit(name="Gym", frequency="daily", hid: UUID | None = None) -> HabitResponse:
    return HabitResponse(
        id=hid or uuid4(),
        user_id=uuid4(),
        name=name,
        description="x",
        frequency=frequency,
        mark_done=False,
        created_at=datetime.now(UTC),
    )


def test_from_at_risk_maps_fields():
    h = make_habit(name="Gym", frequency="daily")
    ctx = CoachContext.from_at_risk([h], {h.id: {"streak": 5, "days_missed": 3}})
    assert len(ctx.at_risk) == 1
    item = ctx.at_risk[0]
    assert (item.name, item.frequency, item.streak, item.days_missed) == ("Gym", "daily", 5, 3)


def test_from_at_risk_skips_habit_without_analytics():
    h1, h2 = make_habit(name="Gym"), make_habit(name="Read")
    ctx = CoachContext.from_at_risk([h1, h2], {h1.id: {"streak": 1, "days_missed": 4}})
    assert [i.name for i in ctx.at_risk] == ["Gym"]  # h2 dropped, no fake 0


def test_from_at_risk_empty():
    ctx = CoachContext.from_at_risk([], {})
    assert ctx.at_risk == []
