# UEFA Champions League Predictor 🏆

A full-stack, automated machine learning pipeline and interactive web application that predicts the outcome of the UEFA Champions League.

This project was built to accurately model UEFA's radically new **2024/25 36-team Swiss-stage format**. By dynamically fetching live real-world match data, calculating custom Elo ratings, and generating an XGBoost probability matrix, the engine runs **10,000 Monte Carlo tournament simulations** in seconds to project the exact probability of every single club reaching each stage of the tournament.

---

## 🧠 The Machine Learning Pipeline

### 1. League-Tier Adjusted Elo System
Standard football Elo systems treat all domestic leagues equally. This model employs a custom initialization logic that mathematically balances the strength of schedule across different European leagues (e.g., weighting the Premier League differently than the Scottish Premiership).

When a new team enters the tournament without historical data, their base Elo is initialized using a tier-weighted formula:

$$ 
R_{initial} = 1300 + (T \times 50) 
$$

*(Where $T$ is the domestic league tier, ranging from 1 to 4).*

During knockout phase tiebreakers (simulating extra time and penalties), the engine reverts to the standard Elo expected-probability formula, factoring in a static $+35$ Elo home-field advantage for the second leg:

$$ 
E_{home} = \frac{1}{1 + 10^{(R_{away} - (R_{home} + 35)) / 400}} 
$$

### 2. XGBoost Probability Matrix
Rather than relying on simple Poisson distributions for goalscoring, the predictor uses an **XGBoost (Extreme Gradient Boosting)** model trained on hundreds of historical Champions League fixtures.
- The model takes two teams and their engineered features (Elo diff, League Tier diff, 5-game smoothed Goal Differentials) as input.
- It outputs a precise 90-minute categorical probability matrix: `(Home Win %, Draw %, Away Win %)`.

To simulate the inherent chaos of the new Swiss Phase (where teams often rotate squads after securing qualification), the model applies **Temperature Scaling** ($T = 1.15$) to the softmax outputs to flatten the distribution and introduce realistic variance:

$$ 
p_i = \frac{p_i^{1/T}}{\sum_j p_j^{1/T}} 
$$

### 3. The Monte Carlo Engine (10,000x Simulations)
The core simulation engine programmatically replicates UEFA's new complex tournament structure 10,000 times to map the variance of the tournament:
- **The Swiss League Phase**: Evaluates all 144 fixtures. Ties in the standings are resolved using a **Jittered Elo Tiebreaker**—simulating the randomness of goal differential by adding Gaussian noise ($\sigma = 75$) to each tied team's Elo rating.
- **The Seed 9-24 Playoff Round**: Mathematically executes the two-legged playoff ties.
- **The Fixed Bracket**: Projects the exact tennis-style knockout tree (Quarter-finals, Semi-finals, Final) based on the seeding from the Swiss phase.

### 4. Live Data Automation (ETL)
The application doesn't just predict the beginning of the season—it is a living, breathing model.
- An automated Python ETL pipeline connects to the `Football-Data API`.
- **Reality-Locking**: As real-world matches finish, the engine parses the JSON, locks in those actual points/results, and restricts the XGBoost random variance *only* to the remaining scheduled fixtures.
- Users can trigger a live synchronization from the UI at any point, instantly pulling the newest scores and re-running 10,000 fresh simulations.

---

## 💻 Tech Stack & Architecture

- **Machine Learning**: `XGBoost`, `scikit-learn`, `pandas`, `numpy`
- **Backend**: `Python`, `FastAPI`, `SQLAlchemy`, `Uvicorn`
- **Database**: `PostgreSQL`
- **Frontend**: `React`, `Vite`, `TailwindCSS v4`, `Axios`
- **Infrastructure**: Fully containerized with `Docker` & `docker-compose`

---

## ✨ Application Features

- **Projection Dashboard**: A sortable, interactive interface detailing the percentage chance of all 36 clubs reaching the Round of 16, Quarters, Semis, and lifting the trophy.
- **Live Bracket Generator**: Watch a single deterministic pathway through the massive 5-column bracket generate in real-time.
- **Head-to-Head Simulator**: Select any two teams in Europe and instantly query the XGBoost model to view visual probability bars for a 90-minute matchup.
- **1-Click Sync**: Click the "Sync Live Data" button to trigger the Python pipeline, download real-world scores, and live-reload the entire app.

---

## 🚀 Getting Started

This entire application is Dockerized. You can spin up the database, the backend, the machine learning models, and the frontend with a single command.

### Prerequisites
- Docker & Docker Desktop installed
- An API Key from [Football-Data.org](https://www.football-data.org/)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/UEFA-Champions-League-Predictor.git
   cd UEFA-Champions-League-Predictor
   ```

2. **Configure your Environment:**
   Create a `.env` file in the root directory and add your API key:
   ```env
   FOOTBALL_API_KEY=your_api_key_here
   ```

3. **Build and spin up the containers:**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the Application!**
   - **Frontend UI**: `http://localhost:3000`
   - **Backend API Docs**: `http://localhost:8000/docs`

---

## 📂 Project Structure

```text
├── src/
│   ├── api/          # FastAPI routes, schemas, and entrypoint
│   ├── data/         # Ingestion scripts for the Football-Data API
│   ├── database/     # SQLAlchemy models and Postgres seeding logic
│   ├── features/     # Feature engineering for the ML pipeline
│   ├── models/       # Model training scripts (XGBoost)
│   └── simulation/   # The core Monte Carlo tournament engine
├── frontend/         # Vite + React + Tailwind frontend application
├── models/           # Serialized model weights (.pkl files)
├── data/             # Local JSON data storage (Raw/Processed)
├── src/pipeline.py   # Master orchestrator for the live-sync ETL task
├── docker-compose.yml
└── Dockerfile
```
