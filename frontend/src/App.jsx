import { useState } from "react";
import SearchBar from "./components/SearchBar";
import AnswerCard from "./components/AnswerCard";
import ResultCard from "./components/ResultCard";
import StatsBar from "./components/StatsBar";
import { useQuery } from "./hooks/useQuery";
import "./App.css";

export default function App() {
  const { loading, result, error, run } = useQuery();
  const [lastQuestion, setLastQuestion] = useState("");

  const handleSearch = (params) => {
    setLastQuestion(params.question);
    run(params);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <path d="m21 16-3 3-3-3" /><path d="M18 19V5" />
            <path d="M3 8l3-3 3 3" /><path d="M6 5v14" />
            <circle cx="12" cy="12" r="2" /><path d="M12 10V3" /><path d="M12 21v-7" />
          </svg>
          <h1>Mining Intelligence</h1>
        </div>
        <StatsBar />
      </header>

      <main className="app-main">
        <div className="hero">
          <h2 className="hero-title">News · Policy · Prices</h2>
          <p className="hero-sub">
            Search across mining news, critical mineral policy, and commodity prices —
            powered by semantic retrieval and AI-generated answers.
          </p>
        </div>

        <SearchBar onSearch={handleSearch} loading={loading} />

        {/* Error */}
        {error && (
          <div className="error-banner">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="loading-state">
            <div className="loading-shimmer" />
            <div className="loading-shimmer short" />
            <div className="loading-shimmer medium" />
            <div className="loading-shimmer" />
            <div className="loading-shimmer short" />
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <div className="results-section">
            <div className="results-meta">
              <strong>&ldquo;{lastQuestion}&rdquo;</strong>
              <span className="meta-sep">·</span>
              <span>{result.retrieved_docs.length} documents found</span>
              <span className="meta-sep">·</span>
              <span>{result.query_time_ms}ms</span>
            </div>

            <AnswerCard answer={result.answer} />

            <div className="results-list">
              {result.retrieved_docs.map((doc, i) => (
                <ResultCard key={doc.id} doc={doc} index={i} />
              ))}
            </div>
          </div>
        )}

        {/* Empty state */}
        {!result && !loading && !error && (
          <div className="empty-state">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" opacity="0.25">
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
            </svg>
            <p>Ask a question above to search the mining intelligence corpus</p>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <span>Mining Intelligence Pipeline</span>
        <span className="footer-sep">·</span>
        <span>7 sources · news / policy / price</span>
        <span className="footer-sep">·</span>
        <span>579 documents indexed</span>
      </footer>
    </div>
  );
}
