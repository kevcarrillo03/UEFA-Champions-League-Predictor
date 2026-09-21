import { useState, useEffect } from "react";
import { getMatchPrediction } from "../api/simulation_service";
import { useSimulationData } from "../hooks/use_simulation_data";
import ProbabilityBar from "./probability_bar";
import crests from "../crests.json";

export default function HeadToHeadView() {
  const { data, loading: teamsLoading } = useSimulationData();
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const teams = data?.results?.map(r => r.Club).sort() || [];

  useEffect(() => {
    if (teams.length > 0 && !homeTeam && !awayTeam) {
      setHomeTeam(teams[0]);
      setAwayTeam(teams[1]);
    }
  }, [teams, homeTeam, awayTeam]);

  const handleSimulate = async () => {
    if (homeTeam === awayTeam) {
      setError("please select two different teams.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await getMatchPrediction(homeTeam, awayTeam);
      setPrediction(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (teamsLoading) return <div className="p-8 text-slate-400 animate-pulse">Loading engine...</div>;

  return (
    <div className="mx-auto max-w-3xl p-6 text-slate-100">
      <div className="mb-8 border-b border-slate-800 pb-6">
        <h2 className="text-3xl font-bold text-white">Match Simulator</h2>
        <p className="text-sm text-slate-400 mt-2">Evaluate 90-minute win probabilities based on current form and Elo.</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mb-8">
        <div className="flex flex-col md:flex-row gap-6 items-end">
          <div className="flex-1 w-full">
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-2">Home Team</label>
            <div className="flex items-center gap-3 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2">
              {crests[homeTeam] && <img src={crests[homeTeam]} className="w-6 h-6 object-contain" alt="" />}
              <select 
                value={homeTeam} 
                onChange={(e) => setHomeTeam(e.target.value)}
                className="w-full bg-transparent text-white focus:outline-none appearance-none"
              >
                {teams.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          
          <div className="text-slate-600 font-bold text-xl pb-2">VS</div>
          
          <div className="flex-1 w-full">
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-2">Away Team</label>
            <div className="flex items-center gap-3 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2">
              {crests[awayTeam] && <img src={crests[awayTeam]} className="w-6 h-6 object-contain" alt="" />}
              <select 
                value={awayTeam} 
                onChange={(e) => setAwayTeam(e.target.value)}
                className="w-full bg-transparent text-white focus:outline-none appearance-none"
              >
                {teams.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          
          <button 
            onClick={handleSimulate}
            disabled={loading}
            className="w-full md:w-auto bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Calculating..." : "Predict"}
          </button>
        </div>
        {error && <p className="text-red-400 mt-4 text-sm font-medium">{error}</p>}
      </div>

      {prediction && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 shadow-2xl">
          <div className="flex justify-center items-center gap-6 mb-10">
            {crests[prediction.home_team] && <img src={crests[prediction.home_team]} className="w-16 h-16 object-contain drop-shadow-xl" alt="" />}
            <h3 className="text-center text-xl font-bold text-white">
              {prediction.home_team} <span className="text-slate-500 font-normal mx-4 text-sm uppercase tracking-widest">vs</span> {prediction.away_team}
            </h3>
            {crests[prediction.away_team] && <img src={crests[prediction.away_team]} className="w-16 h-16 object-contain drop-shadow-xl" alt="" />}
          </div>
          
          <div className="space-y-6 max-w-lg mx-auto">
            <div>
              <div className="flex justify-between text-sm font-medium mb-1">
                <span className="text-slate-300">Home Win ({prediction.home_team})</span>
              </div>
              <ProbabilityBar percentageString={prediction.home_win_pct} colorClass="bg-blue-500" />
            </div>
            
            <div>
              <div className="flex justify-between text-sm font-medium mb-1">
                <span className="text-slate-400">Draw</span>
              </div>
              <ProbabilityBar percentageString={prediction.draw_pct} colorClass="bg-slate-500" />
            </div>
            
            <div>
              <div className="flex justify-between text-sm font-medium mb-1">
                <span className="text-slate-300">Away Win ({prediction.away_team})</span>
              </div>
              <ProbabilityBar percentageString={prediction.away_win_pct} colorClass="bg-emerald-500" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}