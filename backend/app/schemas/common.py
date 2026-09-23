"""Enum values from docs/ARCHITECTURE.md §4.3 and §4.1. Use these exact strings everywhere."""
from typing import Literal

TaskType = Literal["Earth Excavation", "Trenching", "Material Loading", "Grading", "Demolition"]
Weather = Literal["Sunny", "Cloudy", "Windy", "Rainy", "Foggy"]
GroundCondition = Literal["Firm", "Loose", "Wet", "Rocky"]
SkillLevel = Literal["Beginner", "Intermediate", "Expert"]
SeatbeltStatus = Literal["Fastened", "Unfastened"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
Severity = Literal["low", "medium", "high"]
EventType = Literal[
    "proximity_hazard",
    "seatbelt_unfastened",
    "excessive_idling",
    "fuel_spike",
    "abnormal_cycle_time",
    "unsafe_operation",
    "manual_report",
]
AnomalyType = Literal["excessive_idling", "fuel_spike", "abnormal_cycle_time", "unsafe_operation"]
Health = Literal["Good", "Attention", "Critical"]
Scenario = Literal["normal", "seatbelt_off", "proximity_hazard", "excessive_idle", "fuel_spike", "rain"]

# Table-level enums (§4.1)
TaskStatus = Literal["scheduled", "in_progress", "completed"]
IncidentStatus = Literal["open", "resolved"]
TrainingStatus = Literal["not_started", "in_progress", "completed"]
ModuleCategory = Literal["safety", "efficiency", "technique", "incident_response"]
ModuleFormat = Literal["video", "quiz", "simulation", "instructor"]
ShiftName = Literal["Morning", "Evening", "Night"]
MachineType = Literal["Excavator", "Wheel Loader", "Dozer", "Motor Grader"]
Priority = Literal["high", "medium", "low"]
MLMode = Literal["stub", "live"]
