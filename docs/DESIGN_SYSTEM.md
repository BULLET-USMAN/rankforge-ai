# RankForge AI — Enterprise Design System & Visual Guidelines
**Document Version:** 1.0.0  
**Design Identity:** Minimal, Editorial, Modern B2B Enterprise, Dark-First  

---

## 1. Visual Philosophy & Purpose
RankForge AI is engineered as a high-density, authoritative B2B SaaS application. It rejects the generic aesthetic of AI wrappers—characterized by gratuitous neon glows, decorative floating geometric blobs, purple gradients, and fabricated metrics. Instead, the interface adopts a disciplined design system drawing inspiration from high-craft developer and analytics tooling (e.g., Linear, GitHub, and Datadog).

---

## 2. Color Palette & Semantic Tokens

### 2.1 Core Palette

| Role | HEX Code | Tailwind Token | Application |
| :--- | :--- | :--- | :--- |
| **Primary Background** | `#111215` | `bg-rf-bg` | Main canvas background, table track, viewport base |
| **Secondary Background** | `#191A1E` | `bg-rf-bg-secondary` | Sidebars, modal containers, card foundations |
| **Elevated Surfaces** | `#202126` | `bg-rf-surface` | Form inputs, dropdowns, table row hover, pills |
| **Primary Crimson** | `#9F1733` | `text-rf-crimson` / `bg-rf-crimson` | Primary CTA buttons, active sidebar links, key charts |
| **Hover Crimson** | `#B51D3E` | `bg-rf-crimson-hover` | Hover state for primary action buttons |
| **Muted Crimson** | `#6D2233` | `bg-rf-crimson-muted` | Active click state, restrained selection badges |
| **Subtle Borders** | `#34353A` | `border-rf-border` | Container boundaries, card dividers, table separators |
| **Primary Text** | `#E9E9EC` | `text-rf-text` | Page titles, primary headings, tabular values |
| **Secondary Text** | `#92939A` | `text-rf-text-secondary` | Subheadings, input labels, metadata explanations |
| **Muted Text** | `#696A72` | `text-rf-text-muted` | Timestamps, footnote captions, disabled states |

### 2.2 Semantic Feedback Colors

| State | Background | Border | Text | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Success** | `bg-green-950/40` | `border-green-800/40` | `text-green-300` | Verified domains, 200 OK responses, passing checks |
| **Warning** | `bg-amber-950/40` | `border-amber-800/40` | `text-amber-300` | Missing HSTS, slow latency, pending verification |
| **Error** | `bg-red-950/40` | `border-red-800/40` | `text-red-300` | SSRF blocks, connection errors, HTTP 5xx |

---

## 3. Typography & Numerical Formatting
- **Primary Sans:** Inter / Geist (`font-sans`).
- **Monospace:** JetBrains Mono / Geist Mono (`font-mono`). Used for DNS records, verification tokens, JSON keys, and IP addresses.
- **Tabular Numerals (`font-tabular`):** Enforces `font-variant-numeric: tabular-nums` across all metric counters, timestamps, latency values, and scores to prevent layout jitter.
- **Heading Scale:** Restrained hierarchy. Hero titles capped at 48–60px; section headers at 20–24px; card titles at 14–16px.

---

## 4. Layout, Elevation & Grid
- **Spacing System:** Base 8px grid (`p-2`, `p-4`, `p-6`, `p-8`).
- **Corner Radii:** Restrained 6px (`rounded-md`) for controls and inputs; 8px (`rounded-lg`) for cards and dialogs.
- **Elevation:** Zero heavy drop shadows. Depth is achieved entirely through background contrast (`#111215` vs `#191A1E` vs `#202126`) and fine 1px low-contrast borders (`#34353A`).
- **Focus Rings:** High-visibility 2px solid `#9F1733` with 2px offset (`focus-visible:ring-1 focus-visible:ring-rf-crimson`).

---

## 5. Anti-AI Design Rules
1. **Never** use continuous multi-color linear gradients across headings or cards.
2. **Never** apply neon glowing shadows or intense saturated box shadows.
3. **Never** implement arbitrary decorative floating shapes or meaningless sparkle icons.
4. **Never** fabricate SEO scores or fake trend percentages.
5. **Never** include generic placeholder marketing testimonials or fake partner logos.
6. **Always** provide explicit feature states (`available`, `not_configured`, `coming_soon`, or `failed`).
