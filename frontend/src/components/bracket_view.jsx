import { useState, useEffect } from "react";
import apiClient from "../api/client";
import crests from "../crests.json";

export default function BracketView() {
  const [bracket, setBracket] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchBracket = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get("/api/simulations/bracket");
      setBracket(data);
    } catch (err) {
      console.error("Failed to fetch bracket:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBracket();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400 animate-pulse">
        Simulating new tournament path...
      </div>
    );
  }

  if (!bracket) return null;

  const Matchup = ({ match }) => (
    <div className="flex flex-col w-56 bg-slate-900 border border-slate-700 rounded-md overflow-hidden text-sm mb-4 shadow-lg">
      <div className={`px-4 py-3 flex items-center gap-3 ${match.winner === match.team1 ? 'font-bold text-white bg-slate-800' : 'text-slate-400'}`}>
        {crests[match.team1] && <img src={crests[match.team1]} className="w-5 h-5 object-contain" alt="" />}
        <span className="truncate">{match.team1}</span>
      </div>
      <div className="border-t border-slate-800"></div>
      <div className={`px-4 py-3 flex items-center gap-3 ${match.winner === match.team2 ? 'font-bold text-white bg-slate-800' : 'text-slate-400'}`}>
        {crests[match.team2] && <img src={crests[match.team2]} className="w-5 h-5 object-contain" alt="" />}
        <span className="truncate">{match.team2}</span>
      </div>
    </div>
  );

  return (
    <div className="mx-auto max-w-7xl p-6 text-slate-100 overflow-x-auto">
      <div className="flex justify-between items-center mb-12 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white">Live Bracket Simulation</h2>
          <p className="text-sm text-slate-400 mt-2">A single randomized path to the final using the Monte Carlo engine.</p>
        </div>
        <button 
          onClick={fetchBracket} 
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors"
        >
          Rerun Simulation
        </button>
      </div>

      <div className="flex gap-12 min-w-max items-center pb-12">
        {/* playoffs */}
        <div className="flex flex-col gap-2">
          <h3 className="text-slate-500 font-semibold mb-2 uppercase tracking-wider text-xs">Playoffs (Seeds 9-24)</h3>
          {bracket.playoffs.map((m, i) => <Matchup key={i} match={m} />)}
        </div>

        {/* round of 16 */}
        <div className="flex flex-col gap-2">
          <h3 className="text-slate-500 font-semibold mb-2 uppercase tracking-wider text-xs">Round of 16</h3>
          {bracket.round_of_16.map((m, i) => <Matchup key={i} match={m} />)}
        </div>

        {/* quarter-finals */}
        <div className="flex flex-col gap-10">
          <h3 className="text-slate-500 font-semibold mb-2 uppercase tracking-wider text-xs">Quarter-Finals</h3>
          {bracket.quarters.map((m, i) => <Matchup key={i} match={m} />)}
        </div>
        
        {/* semi-finals */}
        <div className="flex flex-col gap-28">
          <h3 className="text-slate-500 font-semibold mb-2 uppercase tracking-wider text-xs">Semi-Finals</h3>
          {bracket.semis.map((m, i) => <Matchup key={i} match={m} />)}
        </div>

        {/* final */}
        <div className="flex flex-col gap-0">
          <h3 className="text-emerald-500 font-semibold mb-2 uppercase tracking-wider text-xs">Final</h3>
          <Matchup match={bracket.final} />
          
          <div className="mt-8 text-center bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-6 shadow-2xl">
            <p className="text-xs text-emerald-500 uppercase tracking-widest mb-2">Champion</p>
            <p className="text-2xl font-bold text-emerald-400">{bracket.final.winner}</p>
          </div>
        </div>
      </div>
    </div>
  );
}