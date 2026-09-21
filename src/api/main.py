import numpy as np
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import random

from src.database.database import SessionLocal
from src.database.models import Team, SimulationRun
from src.api.schemas import TeamResponse, SimulationRunResponse
from src.simulation.simulate_competition import prob_matrix
from src.simulation.simulate_competition import (
    teams_list, get_team_info, get_real_swiss_schedule, 
    simulate_leg, simulate_two_legged_tie, simulate_single_match_neutral
)
from src.pipeline import run_live_sync

app = FastAPI(title="UCL Predictor API")

#cor configs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #I change to ["http://localhost:3000"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/admin/sync")
def sync_live_data():
    try:
        run_live_sync()
        return {"status": "success", "message": "Live data successfully synchronized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/teams", response_model=List[TeamResponse])
def get_all_teams(db: Session = Depends(get_db)):
    #returns all 36 teams with their current Elo ratings and domestic tiers
    teams = db.query(Team).order_by(Team.current_elo.desc()).all()
    return teams

@app.get("/api/teams/{team_name}", response_model=TeamResponse)
def get_team_by_name(team_name: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.name == team_name).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@app.get("/api/simulations/latest", response_model=SimulationRunResponse)
def get_latest_simulation(db: Session = Depends(get_db)):
    latest_run = db.query(SimulationRun).order_by(SimulationRun.run_date.desc()).first()
    if not latest_run:
        raise HTTPException(status_code=404, detail="No simulation runs found")
    return latest_run

@app.get("/api/simulations/bracket")
def get_real_bracket_simulation():
    standings_pts = {t: 0 for t in teams_list}
    fixtures = get_real_swiss_schedule()

    for match in fixtures:
        home = match["home"]
        away = match["away"]
        if match["status"] == "FINISHED":
            if match["winner"] == "HOME_TEAM":
                outcome = 2
            elif match["winner"] == "AWAY_TEAM":
                outcome = 0
            else:
                outcome = 1
        else:
            outcome = simulate_leg(home, away, temperature=1.15) 
            
        if outcome == 2:
            standings_pts[home] += 3
        elif outcome == 1:
            standings_pts[home] += 1
            standings_pts[away] += 1
        else:
            standings_pts[away] += 3

    #ranks the 36 teams with the jittered elo tiebreaker
    standings_ranked = sorted(
        teams_list,
        key=lambda t: (standings_pts[t], get_team_info(t)[0] + np.random.normal(0, 75.0)),
        reverse=True
    )
    
    #index the array so seeds align cleanly (S[1] to S[36])
    S = [None] + standings_ranked

    #simulate Playoff Round seeds 9-24
    playoff_matches = []
    def sim_po(t1, t2):
        w = simulate_two_legged_tie(t1, t2)
        playoff_matches.append({"team1": t1, "team2": t2, "winner": w})
        return w

    PO_9_24 = sim_po(S[9], S[24])
    PO_10_23 = sim_po(S[10], S[23])
    PO_11_22 = sim_po(S[11], S[22])
    PO_12_21 = sim_po(S[12], S[21])
    PO_13_20 = sim_po(S[13], S[20])
    PO_14_19 = sim_po(S[14], S[19])
    PO_15_18 = sim_po(S[15], S[18])
    PO_16_17 = sim_po(S[16], S[17])

    #round of 16 (seeds 1-8 vs playoff winners)
    r16_matches = []
    def sim_r16(t1, t2):
        w = simulate_two_legged_tie(t1, t2)
        r16_matches.append({"team1": t1, "team2": t2, "winner": w})
        return w

    R16_1 = sim_r16(S[1], PO_16_17)
    R16_2 = sim_r16(S[8], PO_9_24)
    R16_3 = sim_r16(S[5], PO_12_21)
    R16_4 = sim_r16(S[4], PO_13_20)
    
    R16_5 = sim_r16(S[3], PO_14_19)
    R16_6 = sim_r16(S[6], PO_11_22)
    R16_7 = sim_r16(S[7], PO_10_23)
    R16_8 = sim_r16(S[2], PO_15_18)

    #quarter-finals
    qf_matches = []
    def sim_qf(t1, t2):
        w = simulate_two_legged_tie(t1, t2)
        qf_matches.append({"team1": t1, "team2": t2, "winner": w})
        return w

    QF1 = sim_qf(R16_1, R16_2)
    QF2 = sim_qf(R16_3, R16_4)
    QF3 = sim_qf(R16_5, R16_6)
    QF4 = sim_qf(R16_7, R16_8)

    #semi-finals
    sf_matches = []
    def sim_sf(t1, t2):
        w = simulate_two_legged_tie(t1, t2)
        sf_matches.append({"team1": t1, "team2": t2, "winner": w})
        return w

    SF1 = sim_sf(QF1, QF2)
    SF2 = sim_sf(QF3, QF4)

    #final
    champ = simulate_single_match_neutral(SF1, SF2)
    final_match = {"team1": SF1, "team2": SF2, "winner": champ}

    return {
        "playoffs": playoff_matches,
        "round_of_16": r16_matches,
        "quarters": qf_matches,
        "semis": sf_matches,
        "final": final_match
    }

@app.get("/api/predict/match")
def predict_head_to_head(home: str, away: str):
    #returns the ml probabilities for a specific matchup.
    if home == away:
        raise HTTPException(status_code=400, detail="teams must be different")
    
    if (home, away) not in prob_matrix:
        raise HTTPException(status_code=404, detail="matchup not found in matrix")
    
    probs = prob_matrix[(home, away)]
    
    return {
        "home_team": home,
        "away_team": away,
        "home_win_pct": f"{probs[2] * 100:.1f}%",
        "draw_pct": f"{probs[1] * 100:.1f}%",
        "away_win_pct": f"{probs[0] * 100:.1f}%"
    }