from pydantic import BaseModel

from app.schemas.common import Scenario


class ScenarioRequest(BaseModel):
    machine_id: str
    scenario: Scenario


class ResetRequest(BaseModel):
    machine_id: str
