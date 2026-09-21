import json
from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import joblib

processed_data_dir = Path("data/processed")
models_dir = Path("models")

model = joblib.load(models_dir/ "xgb_match_predictor.pkl")

with open(models_dir / "model_feature.json", "r", encoding="utf-8") as f:
    feature_columns = json.load(f)
with open(processed_data_dir/ "latest_elo.json", "r", encoding="utf-8") as f:
    latest_elos = json.load(f)
with open(processed_data_dir/ "latest_stats.json", "r", encoding="utf-8") as f:
    latest_stats = json.load(f)

league_tiers = {
    "England": 4.0, "Spain": 4.0, "Italy": 4.0, "Germany": 4.0,
    "France": 3.0, "Netherlands": 3.0, "Portugal": 3.0,
    "Belgium": 2.0, "Scotland": 2.0, "Turkey": 2.0, 
    "DEFAULT": 1.0
}

def load_current_participants(year: int = 2026) -> dict:
    file_path = Path(f"data/raw/CL_{year}_teams.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    participants = {}
    for team in data.get("teams", []):
        name = team.get("name")
        country = team.get("area", {}).get("name", "DEFAULT")
        if name:
            participants[name] = country
    return participants

# Dynamically load the true 36 participants from the 2026/27 API payload
participants_metadata = load_current_participants(2026)

assert len(participants_metadata) == 36

def get_team_info(team: str):
    country = participants_metadata.get(team, "DEFAULT")
    tier = league_tiers.get(country, league_tiers["DEFAULT"])
    elo = latest_elos.get(team, 1300.0 + (tier * 100.0))
    if team not in latest_elos:
        print(f"[WARNING] Team '{team}' has no historical Elo in latest_elo.json. Defaulting to pure prior: {elo:.1f}")
    return elo, tier

#precomputes Pairwise Probabilities
print("Pre-computing pairwise probability matrix for 36 teams...")
teams_list = list(participants_metadata.keys())
prob_matrix = {}

for h_team, a_team in itertools.permutations(teams_list, 2):
    h_elo, h_tier = get_team_info(h_team)
    a_elo, a_tier = get_team_info(a_team)

    h_stats = latest_stats.get(h_team, {"ucl_experience": 0.0, "smoothed_gf": 1.5, "smoothed_ga": 1.5})
    a_stats = latest_stats.get(a_team, {"ucl_experience": 0.0, "smoothed_gf": 1.5, "smoothed_ga": 1.5})

    features = {
        "home_league_tier": h_tier,
        "away_league_tier": a_tier,
        "league_tier_diff": h_tier - a_tier,
        "home_elo": h_elo,
        "away_elo": a_elo,
        "elo_diff": h_elo - a_elo,
        "home_ucl_experience": h_stats["ucl_experience"],
        "away_ucl_experience": a_stats["ucl_experience"],
        "home_smoothed_gf": h_stats["smoothed_gf"],
        "home_smoothed_ga": h_stats["smoothed_ga"],
        "away_smoothed_gf": a_stats["smoothed_gf"],
        "away_smoothed_ga": a_stats["smoothed_ga"],
    }
    input_df = pd.DataFrame([{c: features.get(c, 0.0) for c in feature_columns}])
    #[p(away Win = 0), p(draw = 1), p(home Win = 2)]
    prob_matrix[(h_team, a_team)] = model.predict_proba(input_df)[0]

#pre-sort pots based on Elo
teams_by_elo = sorted(teams_list, key=lambda t: get_team_info(t)[0], reverse=True)
POTS = [
    teams_by_elo[0:9],    #pot 1
    teams_by_elo[9:18],   #pot 2
    teams_by_elo[18:27],  #pot 3
    teams_by_elo[27:36]   #pot 4
]


def get_real_swiss_schedule() -> list[dict]:
    with open("data/raw/CL_2026_matches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    fixtures = []
    for match in data.get("matches", []):
        if match.get("stage") != "LEAGUE_STAGE":
            continue
            
        fixtures.append({
            "home": match["homeTeam"]["name"],
            "away": match["awayTeam"]["name"],
            "status": match["status"],
            "winner": match.get("score", {}).get("winner")
        })
    return fixtures


def simulate_leg(home: str, away: str, temperature: float = 1.0) -> int:
    probs = prob_matrix[(home, away)]
    if temperature != 1.0:
        probs = np.power(probs, 1 / temperature)
        probs /= np.sum(probs)
    return np.random.choice([0, 1, 2], p=probs)


def simulate_two_legged_tie(higher_seed: str, lower_seed: str) -> str:
    #simulates aggregate over two legs: leg 1: lower seed hosts higher seed, leg 2: higher seed hosts lower seed
    res1 = simulate_leg(home=lower_seed, away=higher_seed)
    res2 = simulate_leg(home=higher_seed, away=lower_seed)

    pts_lower = (3 if res1 == 2 else (1 if res1 == 1 else 0)) + (3 if res2 == 0 else (1 if res2 == 1 else 0))
    pts_higher = (3 if res1 == 0 else (1 if res1 == 1 else 0)) + (3 if res2 == 2 else (1 if res2 == 1 else 0))

    if pts_higher > pts_lower:
        return higher_seed
    elif pts_lower > pts_higher:
        return lower_seed
    else:
        #extra time / penalties tiebreaker via relative Elo
        h_elo, _ = get_team_info(higher_seed)
        l_elo, _ = get_team_info(lower_seed)
        
        # Home advantage applied for the higher seed hosting leg 2 over time / pens
        h_elo += 35.0
        
        p_higher = 1.0 / (1.0 + 10.0 ** ((l_elo - h_elo) / 400.0))
        return higher_seed if np.random.rand() < p_higher else lower_seed


def simulate_single_match_neutral(t1: str, t2: str) -> str:
    #simulates the final on a neutral pitch
    p_t1_base = prob_matrix[(t1, t2)][2]
    p_t2_base = prob_matrix[(t2, t1)][2]
    
    #balances probabilities without home advantage
    total = p_t1_base + p_t2_base
    p_t1 = p_t1_base / total
    return t1 if np.random.rand() < p_t1 else t2


def run_full_tournament_simulation(n_simulations: int = 10000):
    print(f"executing {n_simulations:,} full 2026/27 UCL tournament simulations")

    top8_counts = {t: 0 for t in teams_list}
    playoff_counts = {t: 0 for t in teams_list}
    r16_counts = {t: 0 for t in teams_list}
    quarters_counts = {t: 0 for t in teams_list}
    semis_counts = {t: 0 for t in teams_list}
    finalist_counts = {t: 0 for t in teams_list}
    champion_counts = {t: 0 for t in teams_list}
    
    real_schedule = get_real_swiss_schedule()

    for sim in range(n_simulations):
        #league phase
        standings_pts = {t: 0 for t in teams_list}

        for match in real_schedule:
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

        #jittered elo tiebreaker: elo + gaussian noise (sigma = 75)
        standings_ranked = sorted(
            teams_list,
            key=lambda t: (standings_pts[t], get_team_info(t)[0] + np.random.normal(0, 75.0)),
            reverse=True
        )

        top_8 = standings_ranked[0:8]
        playoff_teams = standings_ranked[8:24]
        
        S = [None] + standings_ranked

        for t in top_8:
            top8_counts[t] += 1
        for t in playoff_teams:
            playoff_counts[t] += 1

        PO_9_24 = simulate_two_legged_tie(S[9], S[24])
        PO_10_23 = simulate_two_legged_tie(S[10], S[23])
        PO_11_22 = simulate_two_legged_tie(S[11], S[22])
        PO_12_21 = simulate_two_legged_tie(S[12], S[21])
        PO_13_20 = simulate_two_legged_tie(S[13], S[20])
        PO_14_19 = simulate_two_legged_tie(S[14], S[19])
        PO_15_18 = simulate_two_legged_tie(S[15], S[18])
        PO_16_17 = simulate_two_legged_tie(S[16], S[17])
        
        r16_advancers = top_8 + [PO_9_24, PO_10_23, PO_11_22, PO_12_21, PO_13_20, PO_14_19, PO_15_18, PO_16_17]
        for t in r16_advancers:
            r16_counts[t] += 1

        
        Q1_adv = simulate_two_legged_tie(S[1], PO_16_17)
        Q2_adv = simulate_two_legged_tie(S[8], PO_9_24)
        
        Q3_adv = simulate_two_legged_tie(S[5], PO_12_21)
        Q4_adv = simulate_two_legged_tie(S[4], PO_13_20)
        
        Q5_adv = simulate_two_legged_tie(S[3], PO_14_19)
        Q6_adv = simulate_two_legged_tie(S[6], PO_11_22)
        
        Q7_adv = simulate_two_legged_tie(S[7], PO_10_23)
        Q8_adv = simulate_two_legged_tie(S[2], PO_15_18)
        
        quarters = [Q1_adv, Q2_adv, Q3_adv, Q4_adv, Q5_adv, Q6_adv, Q7_adv, Q8_adv]
        for t in quarters:
            quarters_counts[t] += 1

        
        SF1_adv = simulate_two_legged_tie(Q1_adv, Q2_adv)
        SF2_adv = simulate_two_legged_tie(Q3_adv, Q4_adv)
        
        SF3_adv = simulate_two_legged_tie(Q5_adv, Q6_adv)
        SF4_adv = simulate_two_legged_tie(Q7_adv, Q8_adv)

        semis = [SF1_adv, SF2_adv, SF3_adv, SF4_adv]
        for t in semis:
            semis_counts[t] += 1

        F1_adv = simulate_two_legged_tie(SF1_adv, SF2_adv)
        F2_adv = simulate_two_legged_tie(SF3_adv, SF4_adv)

        finalists = [F1_adv, F2_adv]
        for t in finalists:
            finalist_counts[t] += 1

        champ = simulate_single_match_neutral(finalists[0], finalists[1])
        champion_counts[champ] += 1

    #format results
    results = pd.DataFrame({
        "Club": teams_list,
        "Swiss_Top8": [f"{(top8_counts[t] / n_simulations) * 100:.1f}%" for t in teams_list],
        "R16_Pct": [f"{(r16_counts[t] / n_simulations) * 100:.1f}%" for t in teams_list],
        "Quarters_Pct": [f"{(quarters_counts[t] / n_simulations) * 100:.1f}%" for t in teams_list],
        "Semis_Pct": [f"{(semis_counts[t] / n_simulations) * 100:.1f}%" for t in teams_list],
        "Finalist_Pct": [f"{(finalist_counts[t] / n_simulations) * 100:.1f}%" for t in teams_list],
        "Champion_Pct": [f"{(champion_counts[t] / n_simulations) * 100:.2f}%" for t in teams_list],
        "_raw_champ": [champion_counts[t] for t in teams_list]
    }).sort_values("_raw_champ", ascending=False).drop(columns=["_raw_champ"]).reset_index(drop=True)

    results_json_path = processed_data_dir / "simulation_results.json"
    results.to_json(results_json_path, orient="records", indent=2)
    print(f"\nResults successfully serialized to {results_json_path}")
    
    return results

if __name__ == "__main__":
    results_df = run_full_tournament_simulation(n_simulations=10000)
    print("\n--- 2026/27 Full Tournament Monte Carlo Projections (10,000 runs) ---")
    print(results_df.head(36).to_string(index=False))