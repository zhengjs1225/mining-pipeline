import { useState } from "react";
import { ConfigProvider, Layout, theme, Typography } from "antd";
import SearchBar from "./components/SearchBar";
import AnswerCard from "./components/AnswerCard";
import ResultCard from "./components/ResultCard";
import StatsBar from "./components/StatsBar";
import { useQuery } from "./hooks/useQuery";
import "./App.css";

const { Header, Content, Footer } = Layout;
const { Text } = Typography;

export default function App() {
  const { loading, result, error, run } = useQuery();
  const [lastQuestion, setLastQuestion] = useState("");

  const handleSearch = (params) => {
    setLastQuestion(params.question);
    run(params);
  };

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: "#d4855e",
          borderRadius: 16,
          colorBgContainer: "rgba(26,35,50,.7)",
          colorBgElevated: "rgba(30,45,60,.8)",
          colorBorder: "rgba(255,255,255,.06)",
          colorText: "#eef0f6",
          colorTextSecondary: "#8899bb",
          fontFamily: "'Noto Sans SC', 'Space Grotesk', sans-serif",
          fontSize: 15,
          paddingLG: 20,
        },
      }}
    >
      <Layout className="app-layout">
        {/* ── Header: Soft glass ── */}
        <Header className="app-header">
          <div className="header-left">
            <div className="app-logo">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round">
                <path d="m21 16-3 3-3-3" /><path d="M18 19V5" />
                <path d="M3 8l3-3 3 3" /><path d="M6 5v14" />
                <circle cx="12" cy="12" r="2" />
              </svg>
            </div>
            <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 17, color: "#eef0f6", letterSpacing: "-0.02em" }}>
              Mining Intelligence
            </span>
          </div>
          <StatsBar />
        </Header>

        <Content className="app-content">
          {/* ── Hero ── */}
          <div className="hero">
            <h2 className="hero-title">News · Policy · Prices</h2>
            <p className="hero-sub">
              Search across mining news, critical mineral policy, and commodity
              prices — powered by semantic retrieval and AI-generated answers.
            </p>
          </div>

          {/* ── Search ── */}
          <SearchBar onSearch={handleSearch} loading={loading} />

          {/* ── Error ── */}
          {error && (
            <div className="error-banner">
              <span>{error}</span>
            </div>
          )}

          {/* ── Gemini-style pulsing orb loading ── */}
          {loading && (
            <div className="loading-state">
              <div className="loading-orb" />
              <span className="loading-text">Searching across 7 mining sources...</span>
            </div>
          )}

          {/* ── Results ── */}
          {result && !loading && (
            <div className="results-section">
              <div className="results-meta">
                <Text strong style={{ color: "#eef0f6" }}>
                  &ldquo;{lastQuestion}&rdquo;
                </Text>
                <Text type="secondary">
                  · {result.retrieved_docs.length} docs · {result.query_time_ms}ms
                </Text>
              </div>

              <div className="answer-card">
                <AnswerCard answer={result.answer} />
              </div>

              <div className="results-list">
                {result.retrieved_docs.map((doc, i) => (
                  <div key={doc.id} className="result-card">
                    <ResultCard doc={doc} index={i} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Empty ── */}
          {!result && !loading && !error && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity=".4">
                  <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                </svg>
              </div>
              <Text type="secondary" style={{ fontSize: 15, fontWeight: 300 }}>
                Ask a question above to search the mining intelligence corpus
              </Text>
            </div>
          )}
        </Content>

        <Footer className="app-footer">
          Mining Intelligence Pipeline · 7 sources · news / policy / price
        </Footer>
      </Layout>
    </ConfigProvider>
  );
}
