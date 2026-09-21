# UEFA Champions League Predictor 

A full-stack machine learning pipeline and interactive web application that predicts the outcome of the UEFA Champions League. 

This project accurately models UEFA's new **2024 36-team Swiss-stage format**, dynamically fetching live real-world match data, recalculating Elo ratings, and running **10,000 Monte Carlo bracket simulations** powered by an XGBoost probability matrix.

## Features

- **Live Data Automation**: Fully automated ETL pipeline that syncs with the `Football-Data API`. As real-world matches are played, the engine mathematically locks in those results and re-simulates the remaining tournament.
- **XGBoost Match Predictor**: A trained Gradient Boosting model that evaluates 90-minute win/loss/draw probabilities based on custom domestic league tiering, historical UCL experience, and dynamic Elo ratings.
- **10,000x Monte Carlo Engine**: Accurately simulates the complex UEFA Swiss league format, domestic country-protection draw rules, the Seed 9-24 Playoff Round, and the fixed tennis-style knockout bracket.
- **Interactive Dashboard**: A beautiful, sortable React/Tailwind interface detailing the probability of every single club reaching each stage of the tournament.
- **Live Bracket Generator**: Watch a single deterministic pathway through the bracket generate in real-time, complete with official club crests.
- **Head-to-Head Simulator**: Select any two teams in Europe and instantly calculate their 90-minute win probabilities.

## Architecture

- **Machine Learning**: `XGBoost`, `scikit-learn`, `pandas`, `numpy`
- **Backend**: `Python`, `FastAPI`, `SQLAlchemy`
- **Database**: `PostgreSQL`
- **Frontend**: `React`, `Vite`, `TailwindCSS v4`, `Axios`
- **Infrastructure**: Fully containerized with `Docker` & `docker-compose`

## Getting Started

This entire application is Dockerized for a seamless development experience. 

### Prerequisites
- Docker & Docker Desktop installed
- An API Key from [Football-Data.org](https://www.football-data.org/)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/UEFA-Champions-League-Predictor.git
   cd UEFA-Champions-League-Predictor
   ```

2. Create a `.env` file in the root directory and add your API key:
   ```env
   FOOTBALL_API_KEY=your_api_key_here
   ```

3. Build and spin up the containers:
   ```bash
   docker-compose up --build -d
   ```

4. The application is now running! 
   - **Frontend UI**: `http://localhost:3000`
   - **Backend API Docs**: `http://localhost:8000/docs`

## Project Structure

- `/src/data/` - ETL pipeline that ingests live match payloads from the Football-Data API.
- `/src/features/` - Feature engineering scripts that calculate smoothed goals and Elo diffs.
- `/src/models/` - Training scripts and serialized XGBoost model weights.
- `/src/simulation/` - The core Monte Carlo engine that simulates the UEFA format.
- `/src/api/` - FastAPI backend application exposing endpoints to the frontend.
- `/src/database/` - SQLAlchemy models and automated database seeding logic.
- `/frontend/` - Vite + React application.

