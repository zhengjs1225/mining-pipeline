import { useState, useEffect } from "react";
import {
  Drawer, Form, Input, Select, Switch, Button,
  Space, Typography, Divider, message
} from "antd";
import {
  SettingOutlined, BulbOutlined,
  KeyOutlined, LinkOutlined, RobotOutlined
} from "@ant-design/icons";

const { Text, Title } = Typography;

export default function SettingsDrawer({ open, onClose, isDark, onToggleTheme }) {
  const [config, setConfig] = useState({
    llm_api_key: "",
    llm_base_url: "https://api.deepseek.com/v1",
    llm_model: "deepseek-chat",
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (open) {
      // Load saved config
      const saved_config = localStorage.getItem("mining_config");
      if (saved_config) {
        try { setConfig(JSON.parse(saved_config)); } catch {}
      }
      setSaved(false);
    }
  }, [open]);

  const saveConfig = () => {
    localStorage.setItem("mining_config", JSON.stringify(config));
    setSaved(true);
    message.success("Settings saved — restart server to apply LLM config");
    setTimeout(() => setSaved(false), 2000);
  };

  const maskKey = (key) => {
    if (!key || key.length < 8) return key;
    return key.slice(0, 4) + "****" + key.slice(-4);
  };

  return (
    <Drawer
      title={<span><SettingOutlined /> Settings</span>}
      placement="right"
      width={420}
      open={open}
      onClose={onClose}
      styles={{ body: { padding: "8px 20px 20px" } }}
    >
      <Title level={5} style={{ marginBottom: 16 }}>LLM Configuration</Title>
      <Text type="secondary" style={{ fontSize: 13, display: "block", marginBottom: 16 }}>
        Configure the AI model for answer generation.
      </Text>

                <Form layout="vertical" size="middle">
                  <Form.Item label={<span><KeyOutlined /> API Key</span>}>
                    <Input.Password
                      value={config.llm_api_key}
                      onChange={(e) => setConfig({ ...config, llm_api_key: e.target.value })}
                      placeholder="sk-..."
                      visibilityToggle
                    />
                    {config.llm_api_key && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Current: {maskKey(config.llm_api_key)}
                      </Text>
                    )}
                  </Form.Item>

                  <Form.Item label={<span><LinkOutlined /> Base URL</span>}>
                    <Select
                      value={config.llm_base_url}
                      onChange={(v) => setConfig({ ...config, llm_base_url: v })}
                      options={[
                        { value: "https://api.deepseek.com/v1", label: "DeepSeek" },
                        { value: "https://api.openai.com/v1", label: "OpenAI" },
                        { value: "https://api.anthropic.com/v1", label: "Anthropic" },
                        { value: "", label: "Custom..." },
                      ]}
                    />
                  </Form.Item>

                  <Form.Item label={<span><RobotOutlined /> Model</span>}>
                    <Select
                      value={config.llm_model}
                      onChange={(v) => setConfig({ ...config, llm_model: v })}
                      showSearch
                      options={[
                        { value: "deepseek-chat", label: "DeepSeek Chat" },
                        { value: "deepseek-reasoner", label: "DeepSeek Reasoner" },
                        { value: "gpt-4o-mini", label: "GPT-4o Mini" },
                        { value: "gpt-4o", label: "GPT-4o" },
                        { value: "claude-sonnet-4-6", label: "Claude Sonnet 4.6" },
                        { value: "claude-haiku-4-5", label: "Claude Haiku 4.5" },
                      ]}
                    />
                  </Form.Item>

                  <Button
                    type="primary"
                    onClick={saveConfig}
                    style={{ marginTop: 8 }}
                  >
                    {saved ? "✓ Saved" : "Save Configuration"}
                  </Button>
                </Form>

                <Divider />

                <Title level={5} style={{ marginBottom: 12 }}>Appearance</Title>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <Space>
                    <BulbOutlined />
                    <Text>Dark Mode</Text>
                  </Space>
                  <Switch checked={isDark} onChange={onToggleTheme} />
                </div>
      </Drawer>
  );
}
