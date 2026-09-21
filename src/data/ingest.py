import os
from dotenv import load_dotenv
import json 
import requests
from pathlib import Path
import time

load_dotenv()

API_KEY= os.getenv("FOOTBALL_API_KEY")
BASE_URL="https://api.football-data.org/v4"
HEADERS ={"X-Auth-Token": API_KEY}

def backfill_ChampionsLeague_data(start_yr=2023, current_yr = 2026):
    #fetching historical data(23-26) for training and current schedule

    for season in range (start_yr,current_yr + 1):
        print(f"fetching matches for {season}")

        url= f'{BASE_URL}/competitions/CL/matches?season={season}'
        response = requests.get(url, headers= HEADERS)

        if response.status_code ==200:
            data = response.json()
            outputPath = Path(f"data/raw/CL_{season}_matches.json")
            outputPath.parent.mkdir(parents=True, exist_ok=True)

            with open(outputPath, "w", encoding="utf-8") as f:
                json.dump(data,f,indent=2)
            print(f"saved matches for {season}")
        else:
            print(f"Failed to fetch matches {season}: {response.status_code} - {response.text}")
        time.sleep(6)
        
        print(f"fetching teams for {season}")
        url_teams = f'{BASE_URL}/competitions/CL/teams?season={season}'
        response_teams = requests.get(url_teams, headers=HEADERS)

        if response_teams.status_code == 200:
            data_teams = response_teams.json()
            out_path_teams = Path(f"data/raw/CL_{season}_teams.json")

            with open(out_path_teams, "w", encoding="utf-8") as f:
                json.dump(data_teams, f, indent=2)
            print(f"saved teams for {season}")

        else:
            print(f"Failed to fetch teams {season}: {response_teams.status_code} - {response_teams.text}")
        time.sleep(6)

if __name__ == "__main__":
    backfill_ChampionsLeague_data(start_yr=2023,current_yr=2026)