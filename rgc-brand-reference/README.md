# Really Good Culture — branding and UI reference

Captured 3 October 2026 from [the homepage](https://reallygoodculture.com/) and [the seven-dimensions explorer](https://reallygoodculture.com/seven-dimensions).

## Start here

- Open **index.html** for the visual reference: palette, typography, components, artwork and product UI previews.
- Use **tokens.css** for extracted colours, font stacks and starter components.
- **assets/** contains 70 public image assets, including logos, illustrations, icons and product previews. **asset-manifest.json** records each source URL.
- **source/** contains the downloaded site stylesheet. The JSON extractions and screenshots preserve inspection evidence.

This is a focused design scrape of two public pages and their observed assets. It does not include the authenticated application or every page on the site. Dashboard references are published raster previews; their internal component measurements are not available as live DOM styles.

## Brand character

Restrained typography and dense analytical detail sit alongside playful, tactile 3D imagery. The marketing pages use charcoal fields, oversized regular-weight headings, selective gradient emphasis and rounded calls to action. Product previews use a white sidebar, pale grey workspace, white rounded cards and subtle purple selection states.

## Exact colours from active site styles

| Role | Value |
| --- | --- |
| Charcoal canvas | `#1D1D1D` |
| Dark text on bright surfaces | `#141414` |
| White | `#FFFFFF` |
| Warm contact-section background | `#F4F3EF` |
| Explorer detail panel | `#161618` |
| CTA lime | `#B8F000` |
| CTA green | `#22A651` |
| Indigo token | `#6A6AE2` |
| CTA gradient | `linear-gradient(90deg,#B8F000,#22A651)` |
| Hero text gradient | `linear-gradient(120deg,#C2FF00,#4DC9E2)` |

The stylesheet also contains older/global tokens. The values above come from the active `.rgc-site` scope and current homepage components, checked against computed styles.

### Category colours

The live explorer assigns Product & Retail `#C060B0`, Brand Performance `#4B4BF0`, Culture & Trend `#6060E0`, Market & Macro `#F06040`, Behavioural `#20C070`, Biometric `#40C0C0`, and Synthetic `#C0F000`.

Audience cards use softer pairs: coral `#FFB088 → #F2705A`, blue `#8FD3EC → #4FA8CF`, yellow `#F7DE8A → #EAC24A`, teal `#7FC3B8 → #3E9187`.

## Typography

| Use | Observed styling |
| --- | --- |
| Primary font | Helvetica, Helvetica Neue, Arial, sans-serif |
| Labels / navigation / actions | Menlo, SF Mono, ui-monospace, SFMono-Regular, monospace |
| Accent font | Geist, Helvetica Neue, Arial, sans-serif; used in selected supporting headings |
| Desktop hero | `clamp(80px,6.2vw,92px)`, weight 400, line-height .96, tracking -4px |
| Hero at widths ≤680px | `clamp(38px,10.2vw,56px)`, line-height 1, tracking -1.4px |
| Section heading | `clamp(32px,4vw,58px)`, weight 400, line-height .98, tracking -.045em |
| Card title | 22px / 1.02, weight 400, tracking -.045em |
| Card copy | 15px / 1.3, tracking -.02em, white at 66% |
| Primary action | 14px monospace, weight 500, uppercase, tracking -.02em |
| Eyebrow | 12px monospace, uppercase, tracking .14em |

Inter and Staatliches stylesheet links are loaded too; they are not the main fonts of the inspected marketing UI. Helvetica and Menlo use local/system font fallbacks. No font binaries are included.

## Components and layout

- **Navigation:** sticky, 72px high, 40px horizontal padding; 18px below 680px. Compact logo, ghost pill, gradient pill and menu button.
- **Primary action:** pill radius 999px, padding 13px 26px, dark label over lime/green gradient; rises 1px on hover over .25s.
- **Dark cards:** 22px radius, 24px padding, translucent near-black fill, 1px tinted border and soft shadow. Grid uses four columns, two at ≤680px and one at ≤440px.
- **Explorer panel:** 24px radius, `#161618` fill, white border at 12%, coloured radial glow. Two internal columns become one at ≤680px.
- **Inputs:** white, 12px radius, padding 14px 16px, 1px charcoal border at 16%. Green focus border and a subtle green halo.
- **Form panel:** white, 24px radius, padding 38px 36px, 20px vertical gap, within a warm off-white section.
- **Spacing:** generous marketing section padding, often 110–130px vertically and 40px horizontally; main content widths around 1120–1320px. Card gaps are usually 12–16px.
- **Motion:** scroll reveals use 18px upward travel and .8s easing; stronger variants use 56px travel and scaling. The site includes reduced-motion rules. Category selection changes the accent, panel content and background image; verified by selecting Culture & Trend.

## Artwork and asset guide

- `rgc-logo.png`, `rgc-3d-logo.png`, `rgc-big-noeyes.png`: logo variations.
- `star-3d.webp`, `chain.webp`, `cubes-logo.png`, `squigg-fullwidth.webp`: sculptural brand elements.
- `cereal-*.webp`: small tactile ornaments for audience cards.
- `icon-*.webp` and `color-*.webp`: subdued/coloured dimension icon pairs.
- `ci-*`: capability illustrations and icons.
- `prodretail-screen.png`, `culturetrend-screen.png`, `teams-*-crop.webp`, `mindshare-crop.png`: published product references.
- `bg-*.webp`: atmospheric backgrounds associated with the data dimensions.

Original artwork remains attributed to its source in the manifest. The HTML reference uses the downloaded artwork as reference material.

## Applying this to your tool — design recommendations

These are adaptations, rather than measurements from the live application:

1. Use the light dashboard treatment for prolonged reading: a pale neutral canvas, white cards, subtle separators and dark text. Keep the charcoal treatment for introductions, navigation accents or occasional feature panels.
2. Pair Helvetica-style content with monospace metadata. Use 14–16px for everyday tool text and 12–13px for labels; keep very small marketing tags out of dense task flows.
3. Reserve the lime/green gradient for the most important action. Use the dimension colours consistently for categories, charts and selected states.
4. Use 12px corners for controls and 22–24px corners for large panels. Start with 16–24px interior spacing, reducing the marketing page's large section gaps.
5. Place 3D illustrations in welcome states, category headers or empty states. Keep tables and charts visually quiet.
6. Keep chart labels and status text explicit; colour should support meaning. Add visible keyboard focus and preserve reduced-motion preferences.

### Brief for a designer or builder

Design a practical analytical tool using the Really Good Culture reference pack. Use Helvetica-style headings, Menlo-style metadata, a light neutral workspace, white rounded panels, restrained purple selection states, and a charcoal/white brand frame. Reserve the lime-to-green gradient for primary actions. Use 12px control corners, 22–24px panel corners and consistent 16–24px spacing. Add playful 3D artwork sparingly. Keep the layout readable, responsive and suited to repeated daily use. Refer to tokens.css for verified marketing-site values and to the product preview images for dashboard composition.
