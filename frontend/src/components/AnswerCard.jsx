import { Card, Alert, Typography, Space } from "antd";
import { RobotOutlined, WarningOutlined } from "@ant-design/icons";

const { Text, Paragraph } = Typography;

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
        style={{ marginBottom: 20 }}
      />
    );
  }

  return (
    <Card
      title={
        <Space>
          <RobotOutlined style={{ color: "#1677ff" }} />
          <span style={{ color: "#fff" }}>AI Answer</span>
        </Space>
      }
      style={{
        marginBottom: 20,
        background: "#1a1f3a",
        borderColor: "#2a3a5c",
      }}
      headStyle={{ borderColor: "#2a3a5c", color: "#fff" }}
      bodyStyle={{ padding: "16px 20px" }}
    >
      <Paragraph style={{ color: "#d0d5e0", fontSize: 15, lineHeight: 1.8, margin: 0, whiteSpace: "pre-wrap" }}>
        {answer}
      </Paragraph>
    </Card>
  );
}
