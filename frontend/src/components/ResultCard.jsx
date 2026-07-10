import { Card, Tag, Typography, Progress, Space } from "antd";
import { LinkOutlined } from "@ant-design/icons";

const { Text, Paragraph } = Typography;

const CATEGORY_COLORS = {
  news: "#fa8c16",
  policy: "#1677ff",
  price: "#52c41a",
};

const SOURCE_LABELS = {
  mining_com: "Mining.com",
  sp_global_mining: "S&P Global",
  rare_earth_cn: "中国稀土集团",
  disr_au: "Australia DISR",
  lme: "LME",
  shfe: "SHFE",
  steel_union: "上海钢联",
};

const CATEGORY_ICONS = { news: "📰", policy: "🏛", price: "📈" };

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  } catch {
    return iso.slice(0, 10);
  }
}

function truncate(text, len = 280) {
  if (!text) return "";
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > len ? clean.slice(0, len) + "…" : clean;
}

export default function ResultCard({ doc, index }) {
  const color = CATEGORY_COLORS[doc.category] || "#8c8c8c";
  const score = Math.round(doc.relevance_score * 100);

  return (
    <Card
      size="small"
      style={{
        marginBottom: 12,
        background: "#1a1f3a",
        borderColor: "#2a3a5a",
      }}
      bodyStyle={{ padding: "14px 18px" }}
    >
      <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
        {/* Rank + Score */}
        <div style={{ textAlign: "center", minWidth: 56 }}>
          <Text strong style={{ fontSize: 20, color: color, display: "block", lineHeight: 1 }}>
            #{index + 1}
          </Text>
          <Progress
            type="circle"
            percent={score}
            size={48}
            strokeColor={color}
            trailColor="#232738"
            format={() => (
              <span style={{ color: "#d0d5e0", fontSize: 11, fontWeight: 600 }}>
                {score}%
              </span>
            )}
            strokeWidth={6}
          />
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <Paragraph
            style={{
              marginBottom: 8,
              fontSize: 15,
              fontWeight: 600,
              lineHeight: 1.5,
            }}
          >
            <a
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#e0e6f0" }}
            >
              {CATEGORY_ICONS[doc.category]} {doc.title}
              <LinkOutlined style={{ marginLeft: 6, fontSize: 12, opacity: 0.5 }} />
            </a>
          </Paragraph>

          <Space size={6} wrap style={{ marginBottom: 6 }}>
            <Tag color={color} style={{ margin: 0 }}>
              {doc.category}
            </Tag>
            <Tag style={{ margin: 0, background: "#232738", borderColor: "#2a3050", color: "#a0a8c0" }}>
              {SOURCE_LABELS[doc.source] || doc.source}
            </Tag>
            {doc.published_at && (
              <Tag style={{ margin: 0, background: "transparent", borderColor: "#2a3050", color: "#7880a0" }}>
                {formatDate(doc.published_at)}
              </Tag>
            )}
          </Space>

          <Paragraph
            type="secondary"
            style={{ margin: 0, fontSize: 13, lineHeight: 1.6 }}
            ellipsis={{ rows: 3, expandable: false }}
          >
            {truncate(doc.content_preview)}
          </Paragraph>
        </div>
      </div>
    </Card>
  );
}
