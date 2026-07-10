import { Card, Alert, Typography, Space } from "antd";
import { RobotOutlined, WarningOutlined } from "@ant-design/icons";

const { Paragraph } = Typography;

export default function AnswerCard({ answer }) {
  if (!answer) return null;

  const isWarning = answer.startsWith("⚠");

  if (isWarning) {
    return (
      <Alert
        message="AI Answer"
        description={answer.replace("⚠ ", "")}
        type="warning"
        showIcon
        icon={<WarningOutlined />}
        style={{
          marginBottom: 20,
          borderRadius: 16,
          background: "rgba(255,170,0,.06)",
          border: "1px solid rgba(255,170,0,.15)",
          backdropFilter: "blur(12px)",
        }}
      />
    );
  }

  return (
    <Card
      title={
        <Space>
          <div style={{
            width: 24, height: 24, borderRadius: "50%",
            background: "linear-gradient(135deg, #d4855e 0%, #c9a85c 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <RobotOutlined style={{ color: "#fff", fontSize: 13 }} />
          </div>
          <span style={{ color: "#e8ecf4", fontWeight: 500, fontSize: 15 }}>AI Answer</span>
        </Space>
      }
      style={{ marginBottom: 20 }}
      headStyle={{ borderColor: "rgba(255,255,255,.06)", minHeight: 48 }}
      bodyStyle={{ padding: "16px 20px" }}
    >
      <Paragraph
        className="answer-body"
        style={{ color: "#c8d0e0", margin: 0, whiteSpace: "pre-wrap" }}
      >
        {answer}
      </Paragraph>
    </Card>
  );
}
