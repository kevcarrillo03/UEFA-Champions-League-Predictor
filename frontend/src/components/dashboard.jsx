import { useState, useMemo } from "react";
import crests from "../crests.json";
import { useSimulationData } from "../hooks/use_simulation_data";
import ProbabilityBar from "./probability_bar";

export default function Dashboard() {
  const { data, loading, error } = useSimulationData();
  const [isSyncing, setIsSyncing] = useState(false);
  
  //tracks which column is being sorted and in what direction
  const [sortConfig, setSortConfig] = useState({ key: "Champion_Pct", direction: "desc" });

  const results = data?.results || [];

  //useMemo ensures we only re-sort the array when the data or sort config changes
  const sortedResults = useMemo(() => {
    let sortableItems = [...results];
    
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // If the value is a percentage string, parse it as a float for accurate math sorting
        if (typeof aValue === "string" && aValue.endsWith("%")) {
          aValue = parseFloat(aValue.replace("%", ""));
          bValue = parseFloat(bValue.replace("%", ""));
        }

        if (aValue < bValue) {
          return sortConfig.direction === "asc" ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === "asc" ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [results, sortConfig]);

  //click handler for table headers
  const handleSort = (key) => {
    let direction = "desc";
    if (sortConfig && sortConfig.key === key && sortConfig.direction === "desc") {
      direction = "asc";
    }
    setSortConfig({ key, direction });
  };

  //helper to render the up/down arrow next to the active column
  const getSortIcon = (columnName) => {
    if (sortConfig?.key !== columnName) return null;
    return sortConfig.direction === "asc" ? " ↑" : " ↓";
  };

  if (loading) return <div className="p-8 text-slate-400">Loading model...</div>;
  if (error) return <div className="p-8 text-red-400">Error: {error}</div>;

  return (
    <div className="mx-auto max-w-7xl p-6 text-slate-100">
      <header className="mb-8 border-b border-slate-800 pb-6 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            UCL 2026/27 Projections
          </h1>
          <p className="text-sm text-slate-400 mt-2">
            Based on {data?.n_simulations?.toLocaleString()} Monte Carlo simulations running on an XGBoost probability matrix.
          </p>
        </div>
        <button 
          onClick={async () => {
            if (confirm("Syncing live data takes about 30 seconds to download scores and run 10,000 new simulations. Proceed?")) {
              setIsSyncing(true);
              try {
                const { syncLiveData } = await import("../api/simulation_service");
                await syncLiveData();
                window.location.reload();
              } catch (err) {
                alert("Sync failed: " + err.message);
                setIsSyncing(false);
              }
            }
          }}
          disabled={isSyncing}
          className={`font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            isSyncing 
              ? "bg-emerald-900 text-emerald-400 cursor-not-allowed opacity-80" 
              : "bg-emerald-600 hover:bg-emerald-500 text-white"
          }`}
        >
          {isSyncing ? (
            <>
              <svg className="animate-spin w-4 h-4 text-emerald-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Syncing... (takes ~30s)
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
              Sync Live Data
            </>
          )}
        </button>
      </header>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900 shadow-2xl">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-950 text-xs font-semibold uppercase tracking-wider text-slate-400 select-none">
            <tr>
              <th 
                className="px-6 py-4 cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort("Club")}
              >
                Club{getSortIcon("Club")}
              </th>
              <th 
                className="px-6 py-4 w-48 cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort("Swiss_Top8")}
              >
                Swiss Top 8{getSortIcon("Swiss_Top8")}
              </th>
              <th 
                className="px-6 py-4 w-48 cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort("R16_Pct")}
              >
                Make R16{getSortIcon("R16_Pct")}
              </th>
              <th 
                className="px-6 py-4 w-48 cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort("Semis_Pct")}
              >
                Make Semis{getSortIcon("Semis_Pct")}
              </th>
              <th 
                className="px-6 py-4 w-48 cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort("Champion_Pct")}
              >
                Win Final{getSortIcon("Champion_Pct")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {sortedResults.map((row) => (
              <tr key={row.Club} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-6 py-3 font-semibold text-white flex items-center gap-3">
                  {crests[row.Club] ? (
                    <img src={crests[row.Club]} alt={row.Club} className="w-6 h-6 object-contain" />
                  ) : (
                    <div className="w-6 h-6 bg-slate-800 rounded-full"></div>
                  )}
                  {row.Club}
                </td>
                <td className="px-6 py-3">
                  <ProbabilityBar percentageString={row.Swiss_Top8} colorClass="bg-blue-500" />
                </td>
                <td className="px-6 py-3">
                  <ProbabilityBar percentageString={row.R16_Pct} colorClass="bg-indigo-500" />
                </td>
                <td className="px-6 py-3">
                  <ProbabilityBar percentageString={row.Semis_Pct} colorClass="bg-purple-500" />
                </td>
                <td className="px-6 py-3">
                  <ProbabilityBar percentageString={row.Champion_Pct} colorClass="bg-emerald-500" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}