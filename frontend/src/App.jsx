import { useState, useMemo } from "react";
import { ConfigProvider, Layout, theme, Typography } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import ThemeToggle from "./components/ThemeToggle";
import SettingsDrawer from "./components/SettingsDrawer";
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
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem("theme");
    return saved !== "light";
  });

  const handleSearch = (params) => {
    setLastQuestion(params.question);
    run(params);
  };

  const toggleTheme = () => {
    setIsDark((prev) => {
      const next = !prev;
      localStorage.setItem("theme", next ? "dark" : "light");
      return next;
    });
  };

  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
    document.body.className = loading ? "loading" : "";
  }

  const antTheme = useMemo(
    () => ({
      algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
      token: {
        colorPrimary: isDark ? "#8ab4f8" : "#4a7cf7",
        borderRadius: 20,
        colorBgContainer: isDark ? "#1a1a1e" : "#ffffff",
        colorBgElevated: isDark ? "#222228" : "#f8f8fa",
        colorBorder: isDark ? "#2a2a30" : "#e0e0e4",
        colorText: isDark ? "#f1f1f3" : "#1a1a1e",
        colorTextSecondary: isDark ? "#9a9aa0" : "#5a5a62",
        fontFamily: "'Manrope', 'Noto Sans SC', sans-serif",
        fontSize: 14,
        paddingLG: 18,
      },
    }),
    [isDark]
  );

  return (
    <ConfigProvider theme={antTheme}>
      <Layout className="app-layout">
        {/* ── Header ── */}
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
          <div className="header-right">
            <StatsBar />
            <button className="theme-toggle" onClick={() => setSettingsOpen(true)} title="Settings" aria-label="Settings">
              <SettingOutlined />
            </button>
            <ThemeToggle isDark={isDark} onToggle={toggleTheme} />
          </div>
        </Header>

        {/* ── Settings Drawer ── */}
        <SettingsDrawer
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          isDark={isDark}
          onToggleTheme={toggleTheme}
        />

        {/* ── Main Content ── */}
        <Content className="app-content">
          <div className="hero">
            <h2 className="hero-title">News · Policy · Prices</h2>
            <p className="hero-sub">
              Search mining news, critical mineral policy, and commodity prices
              — powered by semantic retrieval and AI answers
            </p>
          </div>

          <SearchBar onSearch={handleSearch} loading={loading} />

          {error && <div className="error-banner"><span>{error}</span></div>}

          {loading && (
            <div className="loading-state">
              <div className="loading-orb" />
              <span className="loading-text">Searching across sources...</span>
            </div>
          )}

          {result && !loading && (
            <div className="results-section">
              <div className="results-meta">
                <Text strong>&ldquo;{lastQuestion}&rdquo;</Text>
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
