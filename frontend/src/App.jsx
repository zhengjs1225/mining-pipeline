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

  // Add loading class to body for Gemini-style intensified gradient
  if (typeof document !== "undefined") {
    document.body.className = loading ? "loading" : "";
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: "#8ab4f8",
          borderRadius: 20,
          colorBgContainer: "#1a1a1e",
          colorBgElevated: "#222228",
          colorBorder: "#2a2a30",
          colorText: "#f1f1f3",
          colorTextSecondary: "#9a9aa0",
          fontFamily: "'Manrope', 'Noto Sans SC', sans-serif",
          fontSize: 14,
          paddingLG: 18,
        },
      }}
    >
      <Layout className="app-layout">
        {/* Header: Gemini-style ultra minimal */}
        <Header className="app-header">
          <div className="header-left">
            <div className="app-logo">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v4m0 12v4M2 12h4m12 0h4" />
              </svg>
            </div>
            <span className="brand-name">Mining Intelligence</span>
          </div>
          <StatsBar />
        </Header>

        <Content className="app-content">
          {/* Hero: Centered, large, welcoming */}
          <div className="hero">
            <h2 className="hero-title">News · Policy · Prices</h2>
            <p className="hero-sub">
              Search mining news, critical mineral policy, and commodity prices
              — powered by semantic retrieval and AI answers
            </p>
          </div>

          {/* Search */}
          <SearchBar onSearch={handleSearch} loading={loading} />

          {/* Error */}
          {error && (
            <div className="error-banner">
              <span>{error}</span>
            </div>
          )}

          {/* Loading: Gemini pulsating orb */}
          {loading && (
            <div className="loading-state">
              <div className="loading-orb" />
              <span className="loading-text">Searching across sources...</span>
            </div>
          )}

          {/* Results */}
          {result && !loading && (
            <div className="results-section">
              <div className="results-meta">
                <Text strong style={{ color: "#f1f1f3" }}>
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

          {/* Empty */}
          {!result && !loading && !error && (
            <div className="empty-state">
              <div className="empty-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity=".3">
                  <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                </svg>
              </div>
              <Text type="secondary" style={{ fontSize: 14, fontWeight: 400 }}>
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
