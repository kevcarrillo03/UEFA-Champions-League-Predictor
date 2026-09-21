import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from src.database.database import SessionLocal
from src.database.models import Team,Match, SimulationRun

processed_data_dir = Path("data/processed")

def seed_database():
    session = SessionLocal()

    print("clearing existing data")
    session.query(Match).delete()
    session.query(Team).delete()
    session.query(SimulationRun).delete()
    session.commit()

    print("seeding teams")
    matches_df = pd.read_csv(processed_data_dir/"matches_flattened.csv")

    with open(processed_data_dir / "latest_elo.json", "r", encoding="utf-8") as f:
        latest_elos = json.load(f)

    league_tiers={
        "England": 4.0, "Spain": 4.0, "Italy": 4.0, "Germany": 4.0,
        "France": 3.0, "Netherlands": 3.0, "Portugal": 3.0,
        "Belgium": 2.0, "Scotland": 2.0, "Turkey": 2.0, 
        "DEFAULT": 1.0
    }

    teams_data = {}
    for _, row in matches_df.iterrows():
        teams_data[row['home_team']] = row.get('home_country', 'DEFAULT')
        teams_data[row['away_team']] = row.get('away_country', 'DEFAULT')
        
    team_objects = {}
    for name, country in teams_data.items():
        tier = league_tiers.get(country, league_tiers["DEFAULT"])
        elo = latest_elos.get(name, 1300.0 + (tier * 50.0))
        
        team = Team(name=name, country=country, league_tier=tier, current_elo=elo)
        session.add(team)
        team_objects[name] = team
        
    session.commit()
    print(f"Inserted {len(team_objects)} teams.")
    
    print("seeding matches")
    matches_to_insert = []
    for _, row in matches_df.iterrows():
        match = Match(
            match_date=pd.to_datetime(row['match_date']).to_pydatetime(),
            stage=str(row['stage']),
            home_team_id=team_objects[row['home_team']].id,
            away_team_id=team_objects[row['away_team']].id,
            home_goals=int(row['home_goals']),
            away_goals=int(row['away_goals']),
            target=int(row['target'])
        )
        matches_to_insert.append(match)
        
    session.add_all(matches_to_insert)
    session.commit()
    print(f"inserted {len(matches_to_insert)} historical matches")
    
    print("seeding sim results")
    sim_path = processed_data_dir / "simulation_results.json"
    if sim_path.exists():
        with open(sim_path, "r", encoding="utf-8") as f:
            sim_results = json.load(f)
            
        sim_run = SimulationRun(
            n_simulations=10000,
            results=sim_results
        )
        session.add(sim_run)
        session.commit()
        print("inserted latest 10,000-run Monte Carlo projection")
        
    session.close()
    print("\ndatabase seeding complete")

if __name__ == "__main__":
    seed_database()