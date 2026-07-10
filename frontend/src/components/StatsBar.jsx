import { useState, useEffect } from "react";
import * as api from "../lib/api";

export default function StatsBar() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.healthCheck()
      .then((data) => { if (!cancelled) setStats(data); })
      .catch(() => { if (!cancelled) setError(true); });
    const timer = setInterval(() => {
      api.healthCheck()
        .then((data) => { if (!cancelled) setStats(data); })
        .catch(() => {});
    }, 30000);
    return () => { cancelled = true; clearInterval(timer); };
  }, []);

  if (error || !stats) {
    return (
      <div className="stats-bar stats-down">
        <span className="status-dot down" />
        API Offline
      </div>
    );
  }

  const { total_documents, by_category, by_source } = stats;

  const sources = Object.entries(by_source || {}).sort((a, b) => b[1] - a[1]);

  return (
    <div className="stats-bar">
      <div className="stats-main">
        <span className="status-dot up" />
        <span className="stats-total">{total_documents?.toLocaleString()} docs</span>
        <span className="stats-status">live</span>
      </div>

      <div className="stats-cats">
        {by_category && Object.entries(by_category).map(([cat, count]) => (
          <span key={cat} className="stats-chip">
            <span className={`chip-dot cat-${cat}`} />
            {cat} <strong>{count}</strong>
          </span>
        ))}
      </div>

      <div className="stats-sources">
        {sources.slice(0, 5).map(([src, count]) => (
          <span key={src} className="stats-source">
            {src.replace(/_/g, " ")}: {count}
          </span>
        ))}
      </div>
    </div>
  );
}
