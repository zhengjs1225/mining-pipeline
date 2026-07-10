import { useState } from "react";
import { ConfigProvider, Layout, theme, Typography } from "antd";
import { FundOutlined } from "@ant-design/icons";
import SearchBar from "./components/SearchBar";
import AnswerCard from "./components/AnswerCard";
import ResultCard from "./components/ResultCard";
import StatsBar from "./components/StatsBar";
import { useQuery } from "./hooks/useQuery";
import "./App.css";

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

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
          borderRadius: 8,
          colorBgContainer: "#141c2e",
          colorBgElevated: "#1a2440",
          colorBorder: "#1a2a44",
          colorText: "#e8ecf4",
          colorTextSecondary: "#8899bb",
          fontFamily: "'Space Grotesk', 'Noto Sans SC', sans-serif",
          fontSize: 15,
        },
      }}
    >
      <Layout className="app-layout">
        <Header className="app-header">
          <div className="header-left">
            <FundOutlined style={{ fontSize: 22, color: "#d4855e" }} />
            <Title level={4} style={{ margin: 0, color: "#e8ecf4", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, letterSpacing: "-0.02em" }}>
              Mining Intelligence
            </Title>
          </div>
          <StatsBar />
        </Header>

        <Content className="app-content">
          <div className="hero">
            <Title level={2}>
              News · Policy · Prices
            </Title>
            <Text type="secondary" style={{ fontSize: 15 }}>
              Search across mining news, critical mineral policy, and commodity
              prices — powered by semantic retrieval and AI-generated answers.
            </Text>
          </div>

          <SearchBar onSearch={handleSearch} loading={loading} />

          {error && (
            <div className="error-banner">
              <span>{error}</span>
            </div>
          )}

          {loading && (
            <div className="loading-state">
              <div className="loading-shimmer" />
              <div className="loading-shimmer short" />
              <div className="loading-shimmer medium" />
              <div className="loading-shimmer" />
            </div>
          )}

          {result && !loading && (
            <div className="results-section">
              <div className="results-meta">
                <Text strong style={{ color: "#e8ecf4" }}>
                  &ldquo;{lastQuestion}&rdquo;
                </Text>
                <Text type="secondary">
                  {" "}· {result.retrieved_docs.length} docs ·{" "}
                  {result.query_time_ms}ms
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
              <Text type="secondary" style={{ fontSize: 16 }}>
                Ask a question above to search the mining intelligence corpus
              </Text>
            </div>
          )}
        </Content>

        <Footer className="app-footer">
          <Text type="secondary">
            Mining Intelligence Pipeline · 7 sources · news / policy / price
          </Text>
        </Footer>
      </Layout>
    </ConfigProvider>
  );
}
