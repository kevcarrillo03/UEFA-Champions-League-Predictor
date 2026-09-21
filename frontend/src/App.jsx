import { useState } from "react";
import Dashboard from "./components/dashboard";
import BracketView from "./components/bracket_view";
import HeadToHeadView from "./components/headtohead_view";

export default function App() {
  const [currentView, setCurrentView] = useState("dashboard");

  return (
    <div className="min-h-screen bg-slate-950 selection:bg-indigo-500/30 font-sans">
      <nav className="border-b border-slate-800 bg-slate-950 px-6 py-4 sticky top-0 z-10">
        <div className="mx-auto max-w-7xl flex items-center justify-between">
          <div className="text-xl font-bold text-white tracking-tight">UCL Predictor</div>
          <div className="flex gap-2 bg-slate-900 p-1 rounded-lg border border-slate-800 overflow-x-auto">
            <button
              onClick={() => setCurrentView("dashboard")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all whitespace-nowrap ${
                currentView === "dashboard" ? "bg-slate-800 text-white shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              Projections
            </button>
            <button
              onClick={() => setCurrentView("bracket")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all whitespace-nowrap ${
                currentView === "bracket" ? "bg-slate-800 text-white shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              Bracket Generator
            </button>
            <button
              onClick={() => setCurrentView("h2h")}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all whitespace-nowrap ${
                currentView === "h2h" ? "bg-slate-800 text-white shadow-sm" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              Match Simulator
            </button>
          </div>
        </div>
      </nav>

      <main className="pt-4 pb-12">
        {currentView === "dashboard" && <Dashboard />}
        {currentView === "bracket" && <BracketView />}
        {currentView === "h2h" && <HeadToHeadView />}
      </main>
    </div>
  );
}