import { useState, useCallback } from "react";
import * as api from "../lib/api";

export function useQuery() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const run = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.query(params);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, result, error, run };
}
