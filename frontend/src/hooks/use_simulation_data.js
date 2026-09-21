import { useState, useEffect } from "react";
import { getLatestSimulation } from "../api/simulation_service";

export const useSimulationData = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getLatestSimulation();
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSimulation();
  }, []);

  return { data, loading, error, refetch: fetchSimulation };
};