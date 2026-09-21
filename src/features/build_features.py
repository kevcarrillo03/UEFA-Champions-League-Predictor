import pandas as pd
import os
import json
from pathlib import Path
import math

raw_data_dir=Path("data/raw")
processed_data_dir=Path("data/processed")
processed_data_dir.mkdir(parents=True,exist_ok=True)

#league Strength Tiers (4 is highest, 1 is lowest)
league_tiers = {
    "England": 4.0, "Spain": 4.0, "Italy": 4.0, "Germany": 4.0,
    "France": 3.0, "Netherlands": 3.0, "Portugal": 3.0,
    "Belgium": 2.0, "Scotland": 2.0, "Turkey": 2.0, 
    "DEFAULT": 1.0
}

def parse_match_json_to_df(json_file_path: Path) -> pd.DataFrame:
    #flattens a single json file of match data
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("matches", [])
    parsed_data= []

    for m in matches:
        if m.get("status") != "FINISHED":
            continue

        score=m.get("score",{})
        fulltime = score.get("fullTime",{})
        home_goals = fulltime.get("home")
        away_goals = fulltime.get("away")

        if home_goals is None or away_goals is None:
            continue

        if home_goals > away_goals:
            target=2
        elif home_goals == away_goals:
            target=1
        else:
            target=0
            
        parsed_data.append({
            "match_id": m.get("id"),
            "match_date": pd.to_datetime(m.get("utcDate")),
            "stage": m.get("stage"),
            "home_team": m["homeTeam"]["name"],
            "away_team": m["awayTeam"]["name"],
            "home_goals": home_goals,
            "away_goals": away_goals,
            "target": target
        })
        
    return pd.DataFrame(parsed_data)

def load_team_countries():
    #extracts a dictionary mapping team name -> country from the teams JSONs
    team_countries = {}
    for file_name in os.listdir(raw_data_dir):
        if file_name.endswith("_teams.json"):
            file_path = raw_data_dir / file_name
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            teams = data.get("teams", [])
            for t in teams:
                name = t.get("name")
                country = t.get("area", {}).get("name")
                if name and country:
                    team_countries[name] = country
    return team_countries

def build_base_dataset():
    #combines all raw json files from 23-26 into one DF
    all_dfs =[]

    for file_name in os.listdir(raw_data_dir):
        if file_name.endswith("_matches.json"):
            file_path = raw_data_dir / file_name
            df_season = parse_match_json_to_df(file_path)
            all_dfs.append(df_season)

    if not all_dfs:
        print("need to run ingest.py first.")
        return pd.DataFrame()

    combined_df = pd.concat(all_dfs,ignore_index=True)
    combined_df = combined_df.sort_values("match_date").reset_index(drop=True)

    #add country columns
    team_countries = load_team_countries()
    if team_countries:
        combined_df['home_country'] = combined_df['home_team'].map(team_countries)
        combined_df['away_country'] = combined_df['away_team'].map(team_countries)

    output_path= processed_data_dir/ "matches_flattened.csv"
    combined_df.to_csv(output_path,index=False)

    print(f"processed {len(combined_df)} matches")
    print(f"saved on {output_path}")

    return combined_df

def calculate_local_elo(df: pd.DataFrame, k_factor: float = 20.0, home_advantage: float = 80.0) -> tuple[pd.DataFrame, dict]:
    #calculates elo ratings locally based purely on the historical match data I have
    print("Calculating local Elo ratings from match history...")
    
    df = df.sort_values('match_date').reset_index(drop=True)
    
    elo_dict = {} 
    home_elos, away_elos = [], []
    
    elite_clubs = {
        "Manchester City FC": 1850.0, "Real Madrid CF": 1850.0, "FC Bayern München": 1850.0,
        "Paris Saint-Germain FC": 1800.0, "Liverpool FC": 1800.0, "FC Internazionale Milano": 1800.0,
        "Arsenal FC": 1750.0, "FC Barcelona": 1750.0, "Borussia Dortmund": 1750.0,
        "Juventus FC": 1750.0, "Club Atlético de Madrid": 1750.0, "Bayer 04 Leverkusen": 1700.0
    }
    
    for _, row in df.iterrows():
        home, away = row['home_team'], row['away_team']
        hc, ac = row.get('home_country', 'DEFAULT'), row.get('away_country', 'DEFAULT')
        hg, ag = row['home_goals'], row['away_goals']
        target = row['target']

        # Mathematically scale baseline Elo, but cap debutants to prevent them matching elites
        home_tier = league_tiers.get(hc, league_tiers["DEFAULT"])
        away_tier = league_tiers.get(ac, league_tiers["DEFAULT"])
        
        h_baseline = elite_clubs.get(home, 1300.0 + (home_tier * 50.0))
        a_baseline = elite_clubs.get(away, 1300.0 + (away_tier * 50.0))

        home_elo = elo_dict.get(home, h_baseline)
        away_elo = elo_dict.get(away, a_baseline)

        home_elos.append(home_elo)
        away_elos.append(away_elo)

        elo_diff= (home_elo + home_advantage) - away_elo
        expected_home = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
        expected_away = 1.0 - expected_home

        if target == 2: actual_home = 1.0
        elif target == 1: actual_home = 0.5
        else: actual_home = 0.0
        actual_away = 1.0 - actual_home

        #margin of victory multiplier
        margin_mult = math.sqrt(abs(hg - ag)) if hg != ag else 1.0

        elo_dict[home] = home_elo + k_factor * (actual_home - expected_home) * margin_mult
        elo_dict[away] = away_elo + k_factor * (actual_away - expected_away) * margin_mult

    df['home_elo'] = home_elos
    df['away_elo'] = away_elos
    df['elo_diff'] = df['home_elo'] - df['away_elo']
    
    return df, elo_dict

def add_rolling_and_experience_features(df: pd.DataFrame, window: int = 4) -> pd.DataFrame:
    print(f"Calculating smoothed {window}-match form and UCL experience...")
    df = df.sort_values("match_date").reset_index(drop=True)

    home_logs = df[['match_id', 'match_date', 'home_team', 'home_goals', 'away_goals']].rename(
        columns={'home_team': 'team', 'home_goals': 'gf', 'away_goals': 'ga'}
    )
    away_logs = df[['match_id', 'match_date', 'away_team', 'away_goals', 'home_goals']].rename(
        columns={'away_team': 'team', 'away_goals': 'gf', 'home_goals': 'ga'}
    )
    team_logs = pd.concat([home_logs, away_logs]).sort_values("match_date").reset_index(drop=True)

    team_logs['ucl_experience'] = team_logs.groupby('team').cumcount()

    rolling_gf = team_logs.groupby('team')['gf'].transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    rolling_ga = team_logs.groupby('team')['ga'].transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    rolling_count = team_logs.groupby('team')['gf'].transform(lambda s: s.shift(1).rolling(window, min_periods=1).count())

    prior_gf = team_logs['gf'].mean()
    prior_ga = team_logs['ga'].mean()
    m = 3.0  #confidence weight

    rolling_gf = rolling_gf.fillna(prior_gf)
    rolling_ga = rolling_ga.fillna(prior_ga)
    rolling_count = rolling_count.fillna(0)

    #bayesian Shrinkage vectorized
    team_logs['smoothed_gf'] = ((rolling_count * rolling_gf) + (m * prior_gf)) / (rolling_count + m)
    team_logs['smoothed_ga'] = ((rolling_count * rolling_ga) + (m * prior_ga)) / (rolling_count + m)

    rolling_subset = team_logs[['match_id', 'team', 'ucl_experience', 'smoothed_gf', 'smoothed_ga']]

    df = df.merge(
        rolling_subset, left_on=['match_id', 'home_team'], right_on=['match_id', 'team'], how='left'
    ).rename(columns={
        'ucl_experience': 'home_ucl_experience',
        'smoothed_gf': 'home_smoothed_gf',
        'smoothed_ga': 'home_smoothed_ga'
    }).drop(columns=['team'])

    df = df.merge(
        rolling_subset, left_on=['match_id', 'away_team'], right_on=['match_id', 'team'], how='left'
    ).rename(columns={
        'ucl_experience': 'away_ucl_experience',
        'smoothed_gf': 'away_smoothed_gf',
        'smoothed_ga': 'away_smoothed_ga'
    }).drop(columns=['team'])

    return df

def add_league_features(df: pd.DataFrame) -> pd.DataFrame:
    print("Adding domestic league tiers...")
    df['home_league_tier'] = df['home_country'].map(lambda c: league_tiers.get(c, league_tiers["DEFAULT"]))
    df['away_league_tier'] = df['away_country'].map(lambda c: league_tiers.get(c, league_tiers["DEFAULT"]))
    
    df['league_tier_diff'] = df['home_league_tier'] - df['away_league_tier']
    return df
        
def extract_latest_stats(df: pd.DataFrame) -> dict:
    latest_stats = {}
    for team in pd.concat([df['home_team'], df['away_team']]).unique():
        team_matches = df[(df['home_team'] == team) | (df['away_team'] == team)].sort_values('match_date')
        if not team_matches.empty:
            last_match = team_matches.iloc[-1]
            if last_match['home_team'] == team:
                latest_stats[team] = {
                    "ucl_experience": float(last_match['home_ucl_experience']) + 1.0,
                    "smoothed_gf": float(last_match['home_smoothed_gf']),
                    "smoothed_ga": float(last_match['home_smoothed_ga'])
                }
            else:
                latest_stats[team] = {
                    "ucl_experience": float(last_match['away_ucl_experience']) + 1.0,
                    "smoothed_gf": float(last_match['away_smoothed_gf']),
                    "smoothed_ga": float(last_match['away_smoothed_ga'])
                }
    return latest_stats

if __name__ == "__main__":
    base_df = build_base_dataset() #flatten raw jsons

    if base_df.empty:
        exit(1)

    df_with_elo, latest_elos = calculate_local_elo(base_df)
    df_with_rolling = add_rolling_and_experience_features(df_with_elo, window=4)    
    final_df = add_league_features(df_with_rolling)

    output_path = processed_data_dir/ "training_matrix.csv"
    final_df.to_csv(output_path, index=False)

    elo_export_path = processed_data_dir / "latest_elo.json"
    with open(elo_export_path, "w", encoding="utf-8") as f:
        json.dump(latest_elos, f, indent=2)
        
    stats_export_path = processed_data_dir / "latest_stats.json"
    latest_stats = extract_latest_stats(final_df)
    with open(stats_export_path, "w", encoding="utf-8") as f:
        json.dump(latest_stats, f, indent=2)

    print(f"\nFinal Feature Matrix created! {output_path}")
    
    cols_to_print = [c for c in ['match_date', 'home_team', 'home_league_tier', 'away_team', 'away_league_tier', 'league_tier_diff', 'home_elo', 'away_elo', 'elo_diff', 'target'] if c in final_df.columns]
    print(final_df[cols_to_print].head())
