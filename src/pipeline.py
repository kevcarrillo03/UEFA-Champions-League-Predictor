import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.ingest import backfill_ChampionsLeague_data
from src.database.seed_db import seed_database
from src.simulation.simulate_competition import run_full_tournament_simulation

def run_live_sync():
    print("fetch live api data")
    backfill_ChampionsLeague_data(start_yr=2026, current_yr=2026)
    
    print("\nupdating database")
    seed_database()
    
    print("\nrunning monte carlo engine")
    # This will read the new JSON files and run the simulations
    run_full_tournament_simulation(n_simulations=10000)
    
    print("\nsync complete")

if __name__ == "__main__":
    run_live_sync()
