import { useState, useEffect } from "react";
import { Space, Tag, Badge, Typography } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import * as api from "../lib/api";

const { Text } = Typography;

const CATEGORY_COLORS = { news: "#d4855e", policy: "#5599dd", price: "#4dbd8a" };

export default function StatsBar() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(false);

  const fetch = () => {
    api.healthCheck()
      .then((data) => { setStats(data); setError(false); })
      .catch(() => setError(true));
  };

  useEffect(() => {
    fetch();
    const timer = setInterval(fetch, 30000);
    return () => clearInterval(timer);
  }, []);

  if (error || !stats) {
    return (
      <Space size={6}>
        <Badge status="error" />
        <Text type="danger" style={{ fontSize: 13 }}>API Offline</Text>
        <ReloadOutlined style={{ cursor: "pointer" }} onClick={fetch} />
      </Space>
    );
  }

  const { total_documents, by_category } = stats;

  return (
    <Space size={10} wrap>
      <Space size={4}>
        <Badge status="success" />
        <Text type="secondary" style={{ fontSize: 13 }}>
          {total_documents?.toLocaleString()} docs
        </Text>
      </Space>
      {by_category &&
        Object.entries(by_category).map(([cat, count]) => (
          <Tag key={cat} color={CATEGORY_COLORS[cat] || "#8c8c8c"} style={{ margin: 0, fontSize: 12 }}>
            {cat} {count}
          </Tag>
        ))}
    </Space>
  );
}
