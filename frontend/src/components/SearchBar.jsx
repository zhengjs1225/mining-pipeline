import { useState } from "react";

const SOURCES = [
  { key: "", label: "All Sources" },
  { key: "mining_com", label: "Mining.com" },
  { key: "sp_global_mining", label: "S&P Global" },
  { key: "rare_earth_cn", label: "中国稀土" },
  { key: "disr_au", label: "Australia DISR" },
  { key: "lme", label: "LME" },
  { key: "shfe", label: "SHFE" },
  { key: "steel_union", label: "上海钢联" },
];

const CATEGORIES = [
  { key: "", label: "All" },
  { key: "news", label: "News" },
  { key: "policy", label: "Policy" },
  { key: "price", label: "Price" },
];

const EXAMPLES = [
  "LME 铜价最近走势如何？",
  "澳洲锂出口政策有何变化？",
  "中国稀土出口管制政策",
  "iron ore price index trend",
  "latest copper mining developments",
];

export default function SearchBar({ onSearch, loading }) {
  const [question, setQuestion] = useState("");
  const [source, setSource] = useState("");
  const [category, setCategory] = useState("");
  const [topK, setTopK] = useState(5);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    onSearch({ question: question.trim(), topK, sourceFilter: source, categoryFilter: category });
  };

  const handleExample = (q) => {
    setQuestion(q);
    onSearch({ question: q, topK, sourceFilter: source, categoryFilter: category });
  };

  return (
    <div className="search-section">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-row">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about mining — news, policy, or prices..."
            className="search-input"
            autoFocus
          />
          <button type="submit" disabled={loading || !question.trim()} className="search-btn">
            {loading ? (
              <span className="spinner" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            )}
          </button>
        </div>

        <div className="filter-row">
          <select value={source} onChange={(e) => setSource(e.target.value)} className="filter-select">
            {SOURCES.map((s) => (
              <option key={s.key} value={s.key}>{s.label}</option>
            ))}
          </select>

          <select value={category} onChange={(e) => setCategory(e.target.value)} className="filter-select">
            {CATEGORIES.map((c) => (
              <option key={c.key} value={c.key}>{c.label}</option>
            ))}
          </select>

          <select value={topK} onChange={(e) => setTopK(Number(e.target.value))} className="filter-select k-select">
            <option value={3}>Top 3</option>
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
          </select>
        </div>
      </form>

      <div className="examples-row">
        {EXAMPLES.map((q) => (
          <button key={q} onClick={() => handleExample(q)} className="example-chip">
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
