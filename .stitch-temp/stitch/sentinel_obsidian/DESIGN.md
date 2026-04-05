# Design System Specification: The Kinetic Void

## 1. Overview & Creative North Star
### The Creative North Star: "Precision Atmosphere"
This design system moves away from the static, boxy nature of traditional trading platforms. Instead of a rigid grid of spreadsheets, we are building a "Kinetic Void"—a high-fidelity environment where data feels suspended in a three-dimensional space. We achieve this through intentional asymmetry, varying levels of translucency, and an editorial approach to data density. 

The goal is to provide the "Sentinel" (the user) with a cockpit that feels calm yet urgent. We break the "template" look by overlapping glass layers and using a typographic scale that prioritizes "Data as Art," ensuring the most critical market movements command the eye through scale rather than just color.

---

## 2. Colors & Surface Philosophy
The palette is rooted in deep, obsidian tones, using light not as a fill, but as a way to define "physical" presence.

### The "No-Line" Rule
Traditional UI relies on 1px borders to separate content. In this system, **solid borders are prohibited for sectioning.** Boundaries must be defined solely through background color shifts or tonal transitions. To separate a watchlist from a chart, use a transition from `surface` to `surface-container-low`.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked sheets of fine, dark glass. 
- **Base Level:** `surface` (#131315) – The infinite void.
- **Sectioning:** `surface-container-low` (#1c1b1d) – Subtle grouping.
- **Interactive Layers:** `surface-container-high` (#2a2a2c) – Active widgets.
- **Prominent Float:** `surface-container-highest` (#353437) – Modals and pop-overs.

### The "Glass & Gradient" Rule
To create "soul," floating elements (like price alerts or quick-trade panels) must use **Glassmorphism**:
- **Fill:** `surface-variant` (#353437) at 40-60% opacity.
- **Effect:** `backdrop-filter: blur(12px)`.
- **Gradients:** Primary actions should never be flat. Use a linear gradient from `primary` (#adc6ff) to `primary_container` (#4d8eff) at a 135-degree angle to provide a metallic, premium sheen.

---

## 3. Typography: Editorial Authority
We use **Inter** for its neutral, authoritative stance, and **Roboto Mono** (or similar monospaced font) exclusively for ticking data values to prevent "layout jump" during price fluctuations.

- **Display (Large Data):** `display-lg` (3.5rem). Use this for the primary ticker price. It should feel like a headline in a premium financial magazine.
- **Headlines:** `headline-sm` (1.5rem). Use for section titles (e.g., "Portfolio Overview").
- **Labels:** `label-md` (0.75rem). Used for "on_surface_variant" (#c2c6d6) text like "P&L" or "Volume."
- **Data Mono:** All numerical values (Prices, Percentages, Quantities) must use Roboto Mono to ensure vertical alignment across columns.

---

## 4. Elevation & Depth
Hierarchy is achieved through **Tonal Layering** rather than structural lines.

- **The Layering Principle:** Depth is "stacked." Place a `surface-container-lowest` card on a `surface-container-low` section to create a soft, natural lift.
- **Ambient Shadows:** For floating elements (modals), use a shadow with a blur of 40px and 4% opacity, using the `on-surface` color as the shadow tint. This mimics natural light reflecting off a dark surface.
- **The "Ghost Border" Fallback:** If a divider is functionally required for accessibility, use a "Ghost Border": the `outline-variant` (#424754) token at **15% opacity**. Never use 100% opaque lines.

---

## 5. Components

### Buttons
- **Primary:** Gradient fill (`primary` to `primary_container`), `on_primary` text. Border-radius: `md` (0.75rem).
- **Secondary (Bullish/Bearish):** Ghost style. Transparent background, `secondary` (#4edea3) or `tertiary` (#ffb3ad) text, with a 15% opacity Ghost Border of the same color.
- **States:** On hover, increase the `backdrop-filter: blur` or increase the gradient intensity.

### Chips (Market Tags)
Used for sectors (e.g., "Tech," "Energy").
- **Style:** `surface-container-high` background, no border, `label-md` typography.
- **Shape:** `full` (9999px) for a pill shape to contrast against the rectangular cards.

### Input Fields
- **Style:** `surface-container-lowest` fill. 
- **Focus:** Transition the Ghost Border from 15% opacity to 100% `primary` (#adc6ff). 
- **Error:** Use the `error` token (#ffb4ab) for the label text and a subtle glow (shadow) of the same color.

### Cards & Lists
- **The "No-Divider" Rule:** In watchlists, never use horizontal lines. Use 16px of vertical whitespace (Spacing Scale) and a `surface` shift on hover to indicate row selection.
- **Layout:** Use intentional asymmetry. For example, left-align the Asset Name (`title-md`) and right-align the Price and Sparkline, leaving a purposeful "dead zone" in the center to reduce cognitive load.

### Trading-Specific Components
- **The Ticker Sparkline:** A 2px stroke using `secondary` (Gains) or `tertiary` (Losses), with a soft gradient area fill (5% opacity) beneath the line.
- **Depth Map:** Use `secondary_container` and `tertiary_container` for the Bid/Ask volume bars, ensuring they are semi-transparent to allow the background texture to show through.

---

## 6. Do's and Don'ts

### Do:
- Use **Vertical Rhythm**: Ensure all elements align to a 4px or 8px baseline grid to maintain the "High-End Editorial" feel.
- Use **Negative Space**: Allow the "Void" to breathe. High-density data doesn't mean cluttered UI.
- Use **Tonal Shifts**: Use `surface-bright` (#39393b) sparingly to highlight currently active navigation items.

### Don't:
- **No Pure Black:** Never use #000000. It kills the glassmorphic depth. Use `surface_container_lowest` (#0e0e10).
- **No Harsh Borders:** Avoid the 1px white or grey border. It makes the app look like a legacy terminal.
- **No Default Shadows:** Avoid high-opacity, black drop shadows. They look "muddy" on dark themes. Use the Ambient Shadow tinting described in Section 4.
- **No Over-Saturation:** Use `secondary` (Green) and `tertiary` (Red) only for data. Never use them for decorative elements or primary UI buttons.