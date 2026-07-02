---
name: Suprema Elite
colors:
  surface: '#151311'
  surface-dim: '#151311'
  surface-bright: '#3b3936'
  surface-container-lowest: '#100e0c'
  surface-container-low: '#1d1b19'
  surface-container: '#211f1d'
  surface-container-high: '#2c2927'
  surface-container-highest: '#373432'
  on-surface: '#e8e1dd'
  on-surface-variant: '#d7c3b1'
  inverse-surface: '#e8e1dd'
  inverse-on-surface: '#33302e'
  outline: '#9f8e7d'
  outline-variant: '#524437'
  surface-tint: '#ffb869'
  primary: '#ffbf7a'
  on-primary: '#482900'
  primary-container: '#eca045'
  on-primary-container: '#623a00'
  inverse-primary: '#885200'
  secondary: '#cdc5c0'
  on-secondary: '#34302c'
  secondary-container: '#4b4642'
  on-secondary-container: '#bcb4af'
  tertiary: '#87d5ff'
  on-tertiary: '#003548'
  tertiary-container: '#58bbea'
  on-tertiary-container: '#004963'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdcbb'
  primary-fixed-dim: '#ffb869'
  on-primary-fixed: '#2b1700'
  on-primary-fixed-variant: '#673d00'
  secondary-fixed: '#eae1dc'
  secondary-fixed-dim: '#cdc5c0'
  on-secondary-fixed: '#1f1b18'
  on-secondary-fixed-variant: '#4b4642'
  tertiary-fixed: '#c2e8ff'
  tertiary-fixed-dim: '#76d1ff'
  on-tertiary-fixed: '#001e2c'
  on-tertiary-fixed-variant: '#004d67'
  background: '#151311'
  on-background: '#e8e1dd'
  surface-variant: '#373432'
typography:
  display-lg:
    fontFamily: manrope
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: manrope
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: jetbrainsMono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style
The design system embodies a "Soft Dark Mode" aesthetic, pivoting away from harsh obsidian blacks toward a sophisticated, warm-toned landscape. The brand personality is one of quiet luxury, professional excellence, and comfort. It is designed for high-end SaaS or finance platforms where users spend extended periods interacting with complex data.

The style is a fusion of **Minimalism** and **Tactile Modernism**. By utilizing a warm-gray foundation, we reduce the ocular strain typically associated with high-contrast dark modes. The visual language relies on soft elevation, subtle tonal shifts, and a restrained use of metallic-inspired accents to guide the user's eye without causing fatigue.

## Colors
The palette is anchored in organic, warm neutrals. The primary background is a deep, warm-gray that prevents "bleeding" of bright text. 

- **Background (#161412):** The canvas for all views.
- **Surface (#231F1C):** Used for cards, sidebars, and floating panels to create a soft separation from the background.
- **Text (#FAF3E7):** An off-white "cream" that provides high legibility against the dark background without the harshness of pure white.
- **Accent (#ECA045):** A golden ochre used exclusively for high-priority interactive states, active indicators, and critical calls to action.

## Typography
The system uses **Manrope** for its modern, balanced, and highly legible geometric qualities. It feels architectural yet approachable. To complement the technical precision of the "Elite" narrative, **JetBrains Mono** is introduced for labels and metadata, providing a clean, monospaced contrast.

For large headlines, use tighter letter spacing to create a sense of density and importance. Body text should maintain generous line heights (1.5x minimum) to ensure long-form reading comfort within the dark interface.

## Layout & Spacing
This design system utilizes a **Fixed Grid** approach for desktop content (max-width: 1280px) to maintain an air of exclusivity and controlled composition. For mobile, it transitions to a fluid, single-column model.

The spacing rhythm is based on a 4px baseline grid. Use "md" (16px) for standard internal padding and "lg" (24px) for spacing between major components. Margins are intentionally wide on desktop to create a centered, focused experience that emphasizes content quality over quantity.

## Elevation & Depth
In this soft dark aesthetic, elevation is achieved through **Tonal Layers** and extremely **Ambient Shadows**. 

1.  **Base:** #161412 (Lowest level).
2.  **Surface:** #231F1C (Standard cards/containers).
3.  **Overlay:** #2C2824 (Modals, menus, and hovered states).

Shadows should never be pure black. Use a high-blur (20px-40px), low-opacity (15-20%) shadow with a slight brown tint derived from the background color. Borders should be used sparingly; when necessary, use a subtle 1px stroke at 10% opacity of the text color to define edges without creating visual clutter.

## Shapes
The shape language is consistently **Rounded** (0.5rem / 8px). This softens the "Elite" professional tone, making the interface feel more organic and less industrial. Larger containers like cards should use `rounded-lg` (16px) to emphasize the soft containerization of information.

## Components
- **Buttons:** Primary buttons use a subtle gradient of #ECA045 to a slightly darker gold. Secondary buttons should be transparent with a subtle warm-gray border.
- **Input Fields:** Use the Surface color (#231F1C) for the fill. The active state is indicated by a thin #ECA045 bottom border or a subtle outer glow.
- **Cards:** Cards should have no border, relying instead on the tonal shift from the background and a soft ambient shadow for definition.
- **Chips:** Small, pill-shaped elements using a 10% opacity version of the text color as a background for a "ghost" effect.
- **Lists:** Use subtle horizontal dividers (1px, 5% opacity cream) to separate items without breaking the visual flow.
- **Active Indicators:** Use the #ECA045 accent for small pips, underlines, or icons to denote "Current" or "Selected" states.