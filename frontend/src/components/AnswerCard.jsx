import { Card, Typography, Space } from "antd";
import { RobotOutlined } from "@ant-design/icons";

const { Paragraph } = Typography;

export default function AnswerCard({ answer }) {
  if (!answer) return null;

  return (
    <Card
      title={
        <Space>
          <div style={{
            width: 24, height: 24, borderRadius: "50%",
            background: "linear-gradient(135deg, #8ab4f8 0%, #c4a7f8 100%)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <RobotOutlined style={{ color: "#fff", fontSize: 13 }} />
          </div>
          <span style={{ fontWeight: 500, fontSize: 15 }}>AI Answer</span>
        </Space>
      }
      style={{ marginBottom: 20 }}
      headStyle={{ minHeight: 48 }}
      bodyStyle={{ padding: "16px 20px" }}
    >
      <Paragraph className="answer-body" style={{ margin: 0, whiteSpace: "pre-wrap" }}>
        {answer}
      </Paragraph>
    </Card>
  );
}
