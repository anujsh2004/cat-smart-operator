from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas import Context, Machine, Operator, ShiftInfo, WeatherInfo
from app.services import task_service

SHIFT_TIMES = {"Morning": ("08:00", "16:00"), "Evening": ("16:00", "00:00"), "Night": ("00:00", "08:00")}
VISIBILITY = {"Foggy": "Poor", "Rainy": "Reduced"}


def weather_temperature(db: Session, weather: str) -> float:
    """Typical temperature for this weather, from historical sessions."""
    avg = db.scalar(select(func.avg(models.SessionRecord.temperature_c)).where(models.SessionRecord.weather == weather))
    return round(float(avg), 1) if avg is not None else 25.0


def get_context(db: Session, operator_id: str) -> Context | None:
    operator = db.get(models.Operator, operator_id)
    if operator is None:
        return None
    task = task_service.current_task(db, operator_id=operator_id)
    machine = db.get(models.Machine, task.machine_id) if task else db.scalars(select(models.Machine)).first()
    if machine is None:
        return None

    weather = task.weather if task else "Sunny"
    start, end = SHIFT_TIMES.get(operator.shift, ("08:00", "16:00"))
    return Context(
        operator=Operator.model_validate(operator, from_attributes=True),
        machine=Machine.model_validate(machine, from_attributes=True),
        weather=WeatherInfo(
            condition=weather,
            temperature_c=weather_temperature(db, weather),
            visibility=VISIBILITY.get(weather, "Good"),
        ),
        ground_condition=task.ground_condition if task else "Firm",
        shift=ShiftInfo(name=operator.shift, start=start, end=end),
    )
