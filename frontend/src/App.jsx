import { useState } from "react";
import { ConfigProvider, Layout, theme, Typography } from "antd";
import { DatabaseOutlined } from "@ant-design/icons";
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
          colorPrimary: "#1677ff",
          borderRadius: 8,
          colorBgContainer: "#161a2c",
          colorBgElevated: "#1e2340",
          colorBorder: "#2a2f4a",
        },
      }}
    >
      <Layout className="app-layout">
        <Header className="app-header">
          <div className="header-left">
            <DatabaseOutlined style={{ fontSize: 22, color: "#1677ff" }} />
            <Title level={4} style={{ margin: 0, color: "#fff" }}>
              Mining Intelligence
            </Title>
          </div>
          <StatsBar />
        </Header>

        <Content className="app-content">
          <div className="hero">
            <Title level={2} style={{ color: "#fff", marginBottom: 8 }}>
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
                <Text strong style={{ color: "#fff" }}>
                  &ldquo;{lastQuestion}&rdquo;
                </Text>
                <Text type="secondary">
                  {" "}· {result.retrieved_docs.length} docs ·{" "}
                  {result.query_time_ms}ms
                </Text>
              </div>

              <AnswerCard answer={result.answer} />

              <div className="results-list">
                {result.retrieved_docs.map((doc, i) => (
                  <ResultCard key={doc.id} doc={doc} index={i} />
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
