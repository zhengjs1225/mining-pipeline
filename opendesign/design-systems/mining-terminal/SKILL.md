---
name: mining-terminal
description: Industrial mining intelligence design system. Dark geological theme with metallic accents (copper/nickel/lithium/gold). Designed for data-dense dashboards, search interfaces, and analytical tools.
---

# Mining Terminal Design System

**Purpose:** Visual design system for mining intelligence and commodity data applications.

**Tone:** Industrial, authoritative, precise. Geological textures meet terminal aesthetics.

**Differentiation:** Mining-metal accent palette (copper, nickel, zinc, gold, lithium), geological noise background, monospace data display, dark terminal-grade surfaces.

## Color Palette

| Token | Hex | Role |
|-------|-----|------|
| `--accent-copper` | `#d4855e` | Primary accent, buttons, links |
| `--accent-nickel` | `#8a9bad` | Secondary elements |
| `--accent-gold` | `#c9a85c` | Highlights, news category |
| `--accent-lithium` | `#7eb8c9` | Info, tertiary |
| `--cat-news` | `#d4855e` | News category tag |
| `--cat-policy` | `#5599dd` | Policy category tag |
| `--cat-price` | `#4dbd8a` | Price category tag |
| `--bg-deep` | `#0a0e17` | Root background |
| `--bg-primary` | `#0f1624` | Card backgrounds |
| `--bg-elevated` | `#141c2e` | Input backgrounds |

## Typography

| Role | Font | Weight |
|------|------|--------|
| Display/Headings | Space Grotesk | 600-700 |
| Body | Noto Sans SC | 400-500 |
| Data/Numbers | JetBrains Mono | 400-600 |
| CJK | Noto Sans SC | 400-700 |

## Motion

- Entrance: `cubic-bezier(0.16, 1, 0.3, 1)` — smooth deceleration
- Cards stagger: 50ms delay per card
- Search button: subtle pulse glow 3s cycle
- Focus rings: copper glow shadow

## Background

- Deep slate base with geological noise texture (radial gradients)
- Subtle 60px grid overlay with center vignette mask
- Header: frosted glass blur backdrop
