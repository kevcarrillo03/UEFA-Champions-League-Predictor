from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Dict, Any

class TeamBase(BaseModel):
    name: str
    country: str
    league_tier: float
    current_elo: float

class TeamResponse(TeamBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SimulationRunResponse(BaseModel):
    id:int
    run_date: datetime
    n_simulations: int
    results: list[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)