const CATEGORY_COLORS = { news: "#f0a030", policy: "#5599e0", price: "#3dbd7a" };

const SOURCE_LABELS = {
  mining_com: "Mining.com",
  sp_global_mining: "S&P Global",
  rare_earth_cn: "中国稀土集团",
  disr_au: "Australia DISR",
  lme: "LME",
  shfe: "SHFE",
  steel_union: "上海钢联",
};

const CATEGORY_ICONS = {
  news:   "📰",
  policy: "🏛",
  price:  "📈",
};

function formatDate(iso) {
  if (!iso) return "";
  try { return new Date(iso).toLocaleDateString("zh-CN", { year:"numeric", month:"2-digit", day:"2-digit" }); }
  catch { return iso.slice(0,10); }
}

function truncate(text, len = 280) {
  if (!text) return "";
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > len ? clean.slice(0, len) + "…" : clean;
}

export default function ResultCard({ doc, index }) {
  const color = CATEGORY_COLORS[doc.category] || "#6b7280";
  const score = Math.round(doc.relevance_score * 100);

  return (
    <div className="result-card">
      <div className="result-rank">
        <span className="rank-number">{index + 1}</span>
        <div className="score-ring" style={{ background: `conic-gradient(${color} ${score}%, #232738 ${score}%)` }}>
          <span className="score-text">{score}%</span>
        </div>
      </div>

      <div className="result-body">
        <h3 className="result-title">
          <a href={doc.url} target="_blank" rel="noopener noreferrer">
            {CATEGORY_ICONS[doc.category] || "📄"} {doc.title}
          </a>
        </h3>
        <div className="result-meta">
          <span className="meta-tag" style={{ borderColor: color, color, background: `${color}11` }}>
            {doc.category}
          </span>
          <span className="meta-source">{SOURCE_LABELS[doc.source] || doc.source}</span>
          {doc.published_at && <span className="meta-date">{formatDate(doc.published_at)}</span>}
        </div>
        <p className="result-preview">{truncate(doc.content_preview)}</p>
      </div>
    </div>
  );
}
