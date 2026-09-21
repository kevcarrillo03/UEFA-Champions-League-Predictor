from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    #base case for sqlalchemy models
    pass
class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(50))
    league_tier: Mapped[float] = mapped_column(Float)
    current_elo: Mapped[float] = mapped_column(Float)

    #relationships to access match history directly from team object
    home_matches: Mapped[List["Match"]] = relationship(
        "Match", foreign_keys="[Match.home_team_id]", back_populates="home_team"
    )
    away_matches: Mapped[List["Match"]] = relationship(
        "Match", foreign_keys="[Match.away_team_id]", back_populates="away_team"
    )

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    stage: Mapped[str] = mapped_column(String(50))
    
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    
    home_goals: Mapped[int] = mapped_column(Integer)
    away_goals: Mapped[int] = mapped_column(Integer)
    target: Mapped[int] = mapped_column(Integer) 
    
    #relationships back to the team table
    home_team: Mapped["Team"] = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="home_matches"
    )
    away_team: Mapped["Team"] = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_matches"
    )

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    n_simulations: Mapped[int] = mapped_column(Integer, default=10000)
    
    #storing the output array directly as json allows flexible frontend queries
    results: Mapped[dict] = mapped_column(JSON)
