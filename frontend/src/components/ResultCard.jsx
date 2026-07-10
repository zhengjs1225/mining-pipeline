import { Card, Tag, Typography, Progress, Space } from "antd";
import { LinkOutlined } from "@ant-design/icons";

const { Text, Paragraph } = Typography;

const CATEGORY_COLORS = {
  news: "#d4855e",
  policy: "#6b9ce8",
  price: "#5ec4d0",
};

const CATEGORY_LABELS = {
  news: "News",
  policy: "Policy",
  price: "Price",
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

function truncate(text, len = 260) {
  if (!text) return "";
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > len ? clean.slice(0, len) + "…" : clean;
}

export default function ResultCard({ doc, index }) {
  const color = CATEGORY_COLORS[doc.category] || "#6b7280";
  const score = Math.round(doc.relevance_score * 100);

  return (
    <Card
      size="small"
      bodyStyle={{ padding: "16px 20px" }}
    >
      <div style={{ display: "flex", gap: 18, alignItems: "flex-start" }}>
        {/* Score ring */}
        <div style={{ textAlign: "center", minWidth: 52, flexShrink: 0 }}>
          <Progress
            type="circle"
            percent={score}
            size={50}
            strokeColor={{
              "0%": color,
              "100%": color,
            }}
            trailColor="rgba(255,255,255,.05)"
            format={() => (
              <span style={{ color: "#d0d8e8", fontSize: 12, fontWeight: 600, fontFamily: "'JetBrains Mono', monospace" }}>
                {score}
              </span>
            )}
            strokeWidth={5}
          />
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <Paragraph style={{ marginBottom: 8, fontSize: 15, fontWeight: 500, lineHeight: 1.45 }}>
            <a
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#e8ecf4" }}
            >
              {doc.title}
              <LinkOutlined style={{ marginLeft: 6, fontSize: 11, opacity: .4 }} />
            </a>
          </Paragraph>

          <Space size={6} wrap style={{ marginBottom: 8 }}>
            <Tag color={color} style={{ margin: 0, fontSize: 11, fontWeight: 500, borderRadius: 12 }}>
              {CATEGORY_LABELS[doc.category] || doc.category}
            </Tag>
            <Tag style={{ margin: 0, background: "rgba(255,255,255,.04)", border: "1px solid rgba(255,255,255,.08)", color: "#8899bb", fontSize: 11, borderRadius: 12 }}>
              {SOURCE_LABELS[doc.source] || doc.source}
            </Tag>
            {doc.published_at && (
              <Tag style={{ margin: 0, background: "transparent", border: "1px solid rgba(255,255,255,.06)", color: "#667799", fontSize: 11, borderRadius: 12 }}>
                {formatDate(doc.published_at)}
              </Tag>
            )}
          </Space>

          <Paragraph
            type="secondary"
            style={{ margin: 0, fontSize: 13, fontWeight: 300, lineHeight: 1.65 }}
            ellipsis={{ rows: 3, expandable: false }}
          >
            {truncate(doc.content_preview)}
          </Paragraph>
        </div>
      </div>
    </Card>
  );
}
