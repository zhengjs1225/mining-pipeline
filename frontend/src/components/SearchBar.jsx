import { useState } from "react";
import { Input, Select, Button, Space, Tag } from "antd";
import { SearchOutlined, LoadingOutlined } from "@ant-design/icons";

const SOURCES = [
  { value: "", label: "All Sources" },
  { value: "mining_com", label: "Mining.com" },
  { value: "sp_global_mining", label: "S&P Global" },
  { value: "rare_earth_cn", label: "中国稀土" },
  { value: "disr_au", label: "Australia DISR" },
  { value: "lme", label: "LME" },
  { value: "shfe", label: "SHFE" },
  { value: "steel_union", label: "上海钢联" },
];

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "news", label: "News" },
  { value: "policy", label: "Policy" },
  { value: "price", label: "Price" },
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

  const handleSearch = () => {
    if (!question.trim()) return;
    onSearch({
      question: question.trim(),
      topK,
      sourceFilter: source || null,
      categoryFilter: category || null,
    });
  };

  const handleExample = (q) => {
    setQuestion(q);
    onSearch({
      question: q,
      topK,
      sourceFilter: source || null,
      categoryFilter: category || null,
    });
  };

  return (
    <div className="search-section">
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Input.Search
          size="large"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onSearch={handleSearch}
          placeholder="Ask anything about mining — news, policy, or prices..."
          enterButton={
            <Button type="primary" loading={loading} icon={loading ? undefined : <SearchOutlined />}>
              {loading ? "Searching" : "Search"}
            </Button>
          }
          disabled={loading}
          autoFocus
        />

        <Space wrap>
          <Select
            value={source || undefined}
            onChange={setSource}
            options={SOURCES}
            style={{ width: 160 }}
            placeholder="Source"
            allowClear
            onClear={() => setSource("")}
          />
          <Select
            value={category || undefined}
            onChange={setCategory}
            options={CATEGORIES}
            style={{ width: 150 }}
            placeholder="Category"
            allowClear
            onClear={() => setCategory("")}
          />
          <Select
            value={topK}
            onChange={setTopK}
            options={[
              { value: 3, label: "Top 3" },
              { value: 5, label: "Top 5" },
              { value: 10, label: "Top 10" },
            ]}
            style={{ width: 100 }}
          />
        </Space>

        <Space wrap size={[4, 4]}>
          {EXAMPLES.map((q) => (
            <Tag
              key={q}
              color="blue"
              style={{ cursor: "pointer", padding: "4px 10px", fontSize: 13 }}
              onClick={() => handleExample(q)}
            >
              {q}
            </Tag>
          ))}
        </Space>
      </Space>
    </div>
  );
}
