import { SunOutlined, MoonOutlined } from "@ant-design/icons";

export default function ThemeToggle({ isDark, onToggle }) {
  return (
    <button
      className="theme-toggle"
      onClick={onToggle}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      aria-label="Toggle theme"
    >
      {isDark ? <SunOutlined /> : <MoonOutlined />}
    </button>
  );
}
