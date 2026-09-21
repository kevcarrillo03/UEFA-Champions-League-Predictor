import apiClient from "./client";

export const getLatestSimulation = async () => {
  return await apiClient.get("/api/simulations/latest");
};

export const getTeams = async () => {
  return await apiClient.get("/api/teams");
};

export const getTeamByName = async (teamName) => {
  return await apiClient.get(`/api/teams/${encodeURIComponent(teamName)}`);
};

export const getMatchPrediction = async (home, away) => {
  return await apiClient.get(`/api/predict/match?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`);
};

export const syncLiveData = async () => {
  return await apiClient.post("/api/admin/sync");
};