import { useState, useEffect } from "react";
import {
  Card, Form, Input, Select, Button, Switch, Popconfirm,
  Space, Tag, Typography, Divider, message, Empty, Tooltip
} from "antd";
import {
  PlusOutlined, DeleteOutlined, ClockCircleOutlined,
  ReloadOutlined, EditOutlined, CheckOutlined, CloseOutlined,
  ScheduleOutlined
} from "@ant-design/icons";
import * as api from "../lib/api";

const { Text, Paragraph, Title } = Typography;

const CRON_PRESETS = [
  { label: "Every morning (9:00)", value: "0 9 * * *" },
  { label: "Every afternoon (14:00)", value: "0 14 * * *" },
  { label: "Every evening (18:00)", value: "0 18 * * *" },
  { label: "Every hour", value: "0 * * * *" },
  { label: "Every 30 minutes", value: "*/30 * * * *" },
  { label: "Weekdays at 8:00", value: "0 8 * * 1-5" },
  { label: "Monday at 9:00", value: "0 9 * * 1" },
  { label: "Daily at 7:30", value: "30 7 * * *" },
];

function CronPreview({ cron }) {
  if (!cron) return null;
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return <Text type="danger">Invalid cron: need 5 fields</Text>;
  const [m, h, d, mo, dow] = parts;
  const times = [];
  if (m === "0" && h === "*" && d === "*" && mo === "*" && dow === "*") times.push("Every hour");
  else if (m.startsWith("*/") && d === "*") times.push(`Every ${m.slice(2)} min`);
  else {
    const hour = h === "*" ? "every hour" : `at ${h.padStart(2, "0")}:${m.padStart(2, "0")}`;
    times.push(hour);
  }
  if (d !== "*") times.push(`day ${d}`);
  if (dow !== "*") {
    const days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    times.push(dow.split(",").map(x => days[parseInt(x)] || x).join(","));
  }
  return <Text type="secondary" style={{ fontSize: 12 }}>{times.join(" · ")}</Text>;
}

export default function ScheduleManager() {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(null); // null | 'new' | scheduleId
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const data = await api.listSchedules();
      setSchedules(data);
    } catch (e) {
      messageApi.error("Failed to load schedules");
    }
    setLoading(false);
  };

  useEffect(() => { fetchSchedules(); }, []);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editing === "new") {
        await api.createSchedule(values);
        messageApi.success("Schedule created");
      } else {
        await api.updateSchedule(editing, values);
        messageApi.success("Schedule updated");
      }
      setEditing(null);
      form.resetFields();
      fetchSchedules();
    } catch (e) {
      if (e.errorFields) return; // form validation
      messageApi.error("Failed to save schedule");
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteSchedule(id);
      messageApi.success("Schedule deleted");
      fetchSchedules();
    } catch (e) {
      messageApi.error("Failed to delete");
    }
  };

  const handleToggle = async (schedule) => {
    try {
      await api.updateSchedule(schedule.id, { enabled: !schedule.enabled });
      fetchSchedules();
    } catch (e) {
      messageApi.error("Failed to toggle");
    }
  };

  const startEdit = (s) => {
    setEditing(s.id);
    form.setFieldsValue(s);
  };

  return (
    <div style={{ marginTop: 32 }}>
      {contextHolder}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <Space>
          <ScheduleOutlined style={{ fontSize: 18 }} />
          <Title level={5} style={{ margin: 0 }}>Scheduled Tasks</Title>
          <Tag>{schedules.length} active</Tag>
        </Space>
        <Space>
          <Button icon={<ReloadOutlined />} size="small" onClick={fetchSchedules} loading={loading} />
          <Button
            type="primary" size="small" icon={<PlusOutlined />}
            onClick={() => { setEditing("new"); form.resetFields(); }}
            disabled={editing === "new"}
          >
            Add Schedule
          </Button>
        </Space>
      </div>

      {/* Create / Edit form */}
      {editing && (
        <Card size="small" style={{ marginBottom: 16, borderColor: "var(--ring)" }}>
          <Form form={form} layout="vertical" size="small" initialValues={{ top_k: 3, cron: "0 9 * * *", enabled: true }}>
            <Form.Item name="question" label="Query" rules={[{ required: true, message: "Enter a question" }]}>
              <Input placeholder="e.g. LME copper price trend this week" />
            </Form.Item>

            <div style={{ display: "flex", gap: 12 }}>
              <Form.Item name="cron" label="Cron Schedule" style={{ flex: 1 }} rules={[{ required: true }]}>
                <Select
                  options={CRON_PRESETS}
                  placeholder="Select or type cron expression"
                  showSearch
                  allowClear={false}
                />
              </Form.Item>
              <Form.Item name="top_k" label="Results">
                <Select options={[1,2,3,5,10].map(n=>({value:n,label:`Top ${n}`}))} style={{width:90}} />
              </Form.Item>
              <Form.Item name="category_filter" label="Category">
                <Select allowClear placeholder="All" style={{width:100}}
                  options={[{value:"news",label:"News"},{value:"policy",label:"Policy"},{value:"price",label:"Price"}]} />
              </Form.Item>
            </div>

            <Form.Item name="cron" style={{ marginBottom: 6 }}>
              {/* Read-only preview */}
            </Form.Item>
            <CronPreview cron={form.getFieldValue("cron")} />

            <Space style={{ marginTop: 12 }}>
              <Button type="primary" icon={<CheckOutlined />} onClick={handleSubmit}>
                {editing === "new" ? "Create" : "Save"}
              </Button>
              <Button onClick={() => { setEditing(null); form.resetFields(); }}>Cancel</Button>
            </Space>
          </Form>
        </Card>
      )}

      {/* Schedule list */}
      {schedules.length === 0 && !editing ? (
        <Empty description="No schedules yet. Add one to get periodic push notifications." style={{ padding: 32 }} />
      ) : (
        schedules.map((s) => (
          <Card key={s.id} size="small" style={{ marginBottom: 8 }}
            styles={{ body: { padding: "12px 16px" } }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Switch checked={s.enabled} onChange={() => handleToggle(s)} size="small" />
              <div style={{ flex: 1, minWidth: 0 }}>
                <Text strong style={{ fontSize: 14 }}>{s.question}</Text>
                <div style={{ marginTop: 2 }}>
                  <Space size={4} wrap>
                    <Tag icon={<ClockCircleOutlined />} color="blue" style={{ fontSize: 11 }}>
                      {s.cron}
                    </Tag>
                    <CronPreview cron={s.cron} />
                    {s.category_filter && <Tag style={{ fontSize: 11 }}>{s.category_filter}</Tag>}
                    <Tag style={{ fontSize: 11 }}>Top {s.top_k}</Tag>
                    {s.last_run && (
                      <Tooltip title={`Last run: ${s.last_run}`}>
                        <Tag color="green" style={{ fontSize: 11 }}>
                          Ran {new Date(s.last_run).toLocaleString("zh-CN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </Tag>
                      </Tooltip>
                    )}
                  </Space>
                </div>
              </div>
              <Space size={4}>
                <Button size="small" icon={<EditOutlined />} onClick={() => startEdit(s)} disabled={!!editing} />
                <Popconfirm title="Delete this schedule?" onConfirm={() => handleDelete(s.id)}>
                  <Button size="small" danger icon={<DeleteOutlined />} disabled={!!editing} />
                </Popconfirm>
              </Space>
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
