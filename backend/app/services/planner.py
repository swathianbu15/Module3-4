"""
Module 4 core — Planning Engine (no AI required).

This is the deterministic algorithm described in the architecture doc:

    User Data → Planning Algorithm → (optional AI) → Validation → Final Plan

It works even with zero AI configuration, which was the point: the
project shouldn't depend on "send everything to an LLM and hope."

Responsibilities:
1. Figure out which calendar dates are "study days" between start and
   target date, based on the user's available_days.
2. Distribute roadmap topics (each with an estimated_hours cost) across
   those study days, respecting hours_per_day.
3. Break each day's allotted topic time into 2-3 concrete tasks
   (learning / practice / quiz) so the output is immediately usable by
   Module 5 (Daily Tasks) without needing AI at all.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List

from app.schemas.learning_plan import RoadmapTopic

DAY_NAME_BY_WEEKDAY = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


@dataclass
class PlannedTask:
    topic_title: str
    task_title: str
    description: str
    estimated_minutes: int
    task_type: str  # learning | practice | quiz | revision


@dataclass
class PlannedDay:
    day_number: int
    date: date
    tasks: List[PlannedTask] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        return sum(t.estimated_minutes for t in self.tasks)


def get_study_dates(
    start_date: date, target_date: date, available_days: List[str]
) -> List[date]:
    """
    Return every calendar date between start_date and target_date
    (inclusive) whose weekday name is in available_days.
    """
    if target_date < start_date:
        raise ValueError("target_date must be after start_date")

    available_set = set(available_days)
    dates = []
    current = start_date
    while current <= target_date:
        if DAY_NAME_BY_WEEKDAY[current.weekday()] in available_set:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def distribute_topics_across_days(
    topics: List[RoadmapTopic],
    study_dates: List[date],
    hours_per_day: int,
    known_topic_ids: List[int] = None,
) -> List[PlannedDay]:
    """
    Greedily fill each study day up to hours_per_day worth of topic time,
    moving to the next topic once the current one's estimated_hours is
    used up. If the roadmap has more workload than available time fits,
    remaining topics get compressed into the last available days rather
    than silently dropped (with a note in validate_plan).

    known_topic_ids: topics the user already knows (per Module 3 setup)
    are skipped entirely — no tasks generated for them, and their
    estimated_hours don't count against the schedule. This implements
    the "can skip topics the user already knows" feature from the spec.
    """
    if not study_dates:
        raise ValueError(
            "No study days fall between start_date and target_date given "
            "the selected available_days — widen the date range or add "
            "more available days."
        )

    known_ids = set(known_topic_ids or [])
    topics = [t for t in topics if t.id not in known_ids]

    if not topics:
        # Everything was already known — return empty but valid days.
        return [
            PlannedDay(day_number=i + 1, date=d) for i, d in enumerate(study_dates)
        ]

    daily_capacity_minutes = hours_per_day * 60

    days: List[PlannedDay] = [
        PlannedDay(day_number=i + 1, date=d) for i, d in enumerate(study_dates)
    ]

    # Flatten topics into a queue of (topic, remaining_minutes)
    topic_queue = [(t, int(t.estimated_hours * 60)) for t in topics]

    day_index = 0
    remaining_today = daily_capacity_minutes

    for topic, remaining_minutes in topic_queue:
        while remaining_minutes > 0:
            if day_index >= len(days):
                # Ran out of days — compress the rest into the final day
                # rather than losing the content. validate_plan() will
                # flag this as an overload warning.
                final_day = days[-1]
                final_day.tasks.append(
                    PlannedTask(
                        topic_title=topic.title,
                        task_title=f"{topic.title} (compressed — behind schedule)",
                        description=(
                            f"Workload exceeded available time; covering the "
                            f"remainder of {topic.title} here."
                        ),
                        estimated_minutes=remaining_minutes,
                        task_type="learning",
                    )
                )
                remaining_minutes = 0
                continue

            if remaining_today <= 0:
                day_index += 1
                remaining_today = daily_capacity_minutes
                continue

            chunk = min(remaining_minutes, remaining_today)
            days[day_index].tasks.extend(
                _build_tasks_for_chunk(topic.title, chunk)
            )
            remaining_minutes -= chunk
            remaining_today -= chunk

    return days


def _build_tasks_for_chunk(topic_title: str, chunk_minutes: int) -> List[PlannedTask]:
    """
    Split a block of time allotted to one topic into concrete tasks:
    ~60% learning, ~25% practice, ~15% quiz (min 15 min per task, and
    small chunks just become a single "learning" task).
    """
    if chunk_minutes < 30:
        return [
            PlannedTask(
                topic_title=topic_title,
                task_title=f"Continue {topic_title}",
                description=f"Study session covering {topic_title}.",
                estimated_minutes=chunk_minutes,
                task_type="learning",
            )
        ]

    learning_minutes = max(15, round(chunk_minutes * 0.6))
    practice_minutes = max(15, round(chunk_minutes * 0.25))
    quiz_minutes = max(0, chunk_minutes - learning_minutes - practice_minutes)

    tasks = [
        PlannedTask(
            topic_title=topic_title,
            task_title=f"Learn {topic_title}",
            description=f"Core concepts and study material for {topic_title}.",
            estimated_minutes=learning_minutes,
            task_type="learning",
        ),
        PlannedTask(
            topic_title=topic_title,
            task_title=f"Practice {topic_title}",
            description=f"Hands-on exercises applying {topic_title}.",
            estimated_minutes=practice_minutes,
            task_type="practice",
        ),
    ]
    if quiz_minutes >= 10:
        tasks.append(
            PlannedTask(
                topic_title=topic_title,
                task_title=f"{topic_title} quiz",
                description=f"Short quiz to check understanding of {topic_title}.",
                estimated_minutes=quiz_minutes,
                task_type="quiz",
            )
        )
    else:
        # fold leftover minutes into practice rather than a tiny quiz
        tasks[1].estimated_minutes += quiz_minutes

    return tasks


def validate_plan(
    days: List[PlannedDay], topics: List[RoadmapTopic]
) -> List[str]:
    """
    Sanity-check the generated plan and return a list of human-readable
    warnings (empty list = all good). This is the "Validation" step in
    the architecture diagram — it doesn't block plan creation, but the
    warnings should be surfaced to the user/frontend.
    """
    warnings = []

    total_workload_minutes = sum(int(t.estimated_hours * 60) for t in topics)
    total_scheduled_minutes = sum(d.total_minutes for d in days)

    if total_scheduled_minutes < total_workload_minutes:
        warnings.append(
            "Some workload could not fit before the target date and was "
            "compressed into the final study day(s). Consider extending "
            "the target date or increasing hours/day."
        )

    any_compressed = any(
        "compressed" in t.task_title for d in days for t in d.tasks
    )
    if any_compressed and not any(
        "compressed" in w for w in warnings
    ):
        warnings.append(
            "One or more days contain compressed tasks due to a tight schedule."
        )

    if not days:
        warnings.append("No study days were generated.")

    return warnings
