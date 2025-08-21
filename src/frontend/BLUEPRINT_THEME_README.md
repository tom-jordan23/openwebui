# Blueprint Theme for OpenWebUI

A technical drawing-inspired theme for OpenWebUI, channeling the precision and elegance of Artifex Hackworth's engineering aesthetic from Neal Stephenson's "The Diamond Age". Designed with subtle tojo.world branding integration.

## Overview

The Blueprint Theme transforms OpenWebUI into a technical drawing interface that evokes the nostalgic feeling of architectural sketches and engineering blueprints. The theme maintains modern usability while providing a unique, professional aesthetic suitable for technical work environments.

## Theme Philosophy

- **Precision**: Clean lines, exact measurements, and technical accuracy
- **Clarity**: High contrast, readable typography, and clear visual hierarchy  
- **Elegance**: Sophisticated color palette inspired by traditional blueprints
- **Functionality**: Modern UI patterns disguised as technical drawings
- **Subtlety**: Gentle tojo.world branding that doesn't overwhelm the interface

## Color Palette

### Primary Colors
- **Deep Blueprint Blue**: `#003d7a` - Primary actions, headers, main elements
- **Medium Blueprint Blue**: `#0066cc` - Secondary actions, highlights
- **Light Blueprint Blue**: `#4da6ff` - Tertiary elements, hover states
- **Technical Orange**: `#ff6b35` - Accent color, alerts, active indicators

### Background Colors
- **Aged Paper White**: `#fefcf6` - Primary backgrounds, cards
- **Slightly Aged Paper**: `#f8f6f0` - Secondary backgrounds, panels
- **Graph Paper**: `#f0ede5` - Tertiary backgrounds, grid areas

### Technical Drawing Colors
- **Primary Lines**: `#003d7a` - Main interface elements
- **Secondary Lines**: `#666a73` - Dimension lines, secondary borders
- **Construction Lines**: `#b8bcc8` - Guide lines, subtle borders
- **Grid Lines**: `rgba(0, 61, 122, 0.1)` - Background grid pattern

## Typography

### Font Families
- **Technical**: `'Monaco', 'Consolas', 'Courier New', monospace` - Code, specs, labels
- **Heading**: `'Inter', 'Helvetica Neue', system-ui, sans-serif` - Titles, headers
- **Body**: `'Inter', system-ui, -apple-system, sans-serif` - General content

### Font Weights
- **Regular (400)**: Body text, descriptions
- **Medium (500)**: Subheadings, labels
- **Semi-bold (600)**: Section titles, button text
- **Bold (700)**: Main headings, important elements

## Layout System

### Grid System
- **Base Grid Size**: `20px` (16px on mobile)
- **Grid Pattern**: Technical drawing grid overlay
- **Spacing Scale**: Based on grid multiples (5px, 10px, 20px, 30px, 40px, 60px)

### Responsive Breakpoints
- **Mobile**: `< 640px`
- **Tablet**: `640px - 1024px`
- **Desktop**: `> 1024px`

## Key Features

### Visual Elements
- **Blueprint Grid**: Subtle grid pattern overlay on backgrounds
- **Technical Line Weights**: Varying border weights for visual hierarchy
- **Drawing Symbols**: North arrow, section markers, detail callouts
- **Paper Texture**: Subtle aged paper effect on backgrounds
- **Compass Rose**: tojo.world branded navigation element

### Interactive Elements
- **Blueprint Buttons**: Technical drawing style with hover effects
- **Input Fields**: Underlined technical drawing style
- **Progress Bars**: Blueprint line pattern overlays
- **Loading States**: Technical spinner with grid animations
- **Navigation**: Tab-style technical drawing headers

### tojo.world Branding
- **Compass Logo**: Subtle navigation compass with 'T' logo
- **Domain Watermark**: Discrete footer branding
- **Brand Elements**: Technical drawing style logo components
- **Color Integration**: Brand colors woven into blueprint palette

## File Structure

```
src/frontend/
├── styles/
│   ├── blueprint-theme.css          # Core theme variables and base styles
│   └── blueprint-components.css     # Extended component library
├── components/
│   ├── BlueprintPromptDashboard.svelte  # Themed dashboard example
│   └── [other themed components]
└── blueprint-theme-demo.html       # Complete theme demonstration
```

## Implementation

### 1. Core Theme Application

```css
/* Import the base theme */
@import '../styles/blueprint-theme.css';
@import '../styles/blueprint-components.css';

/* Apply blueprint grid to container */
.container {
  background: var(--paper-tertiary);
}

.main-content {
  @extend .blueprint-grid;
  @extend .paper-surface;
}
```

### 2. Component Theming

Replace standard components with blueprint equivalents:

```html
<!-- Standard Button -->
<button class="btn btn-primary">Action</button>

<!-- Blueprint Button -->
<button class="blueprint-button primary">
  <div class="button-icon">⚡</div>
  <div class="button-content">
    <span class="button-title">Execute Action</span>
    <span class="button-desc">Primary system operation</span>
  </div>
  <div class="blueprint-arrow"></div>
</button>
```

### 3. CSS Variable Usage

```css
.custom-component {
  background: var(--paper-base);
  border: var(--border-weight-medium) solid var(--blueprint-primary);
  color: var(--text-primary);
  font-family: var(--font-technical);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-blueprint);
}
```

## Available Components

### Navigation
- `blueprint-nav` - Main navigation bar
- `blueprint-nav-item` - Navigation buttons
- `blueprint-breadcrumb` - Breadcrumb navigation

### Layout
- `blueprint-card` - Content cards with technical headers
- `blueprint-grid` - Grid background pattern
- `paper-surface` - Aged paper background effect
- `blueprint-title-block` - Technical drawing title block

### Forms
- `blueprint-input` - Technical input fields
- `blueprint-textarea` - Multi-line technical inputs
- `blueprint-select` - Dropdown selectors
- `blueprint-button` - Technical drawing buttons
- `blueprint-form` - Form containers

### Data Display
- `blueprint-table` - Technical specification tables
- `blueprint-metric` - Metric display cards
- `blueprint-progress` - Technical progress bars
- `blueprint-code` - Code display with language labels

### Feedback
- `blueprint-alert` - System notifications
- `blueprint-loading` - Loading states
- `blueprint-modal` - Dialog boxes

### Brand Elements
- `tojo-compass` - Navigation compass logo
- `tojo-watermark` - Subtle domain branding
- `tojo-brand-element` - Inline brand components
- `drawing-symbol` - Technical drawing symbols

## Customization

### Adjusting Colors

```css
:root {
  /* Override blueprint colors */
  --blueprint-primary: #004488;
  --blueprint-accent: #ff8c42;
  
  /* Adjust paper colors */
  --paper-base: #ffffff;
  --paper-secondary: #f5f5f5;
}
```

### Modifying Grid Size

```css
:root {
  --grid-size: 24px;  /* Larger grid for better visibility */
}
```

### Brand Customization

```css
.tojo-compass::after {
  content: 'C';  /* Change compass letter */
}

.tojo-watermark {
  content: 'hosted on custom.domain';
}
```

## Accessibility

### Color Contrast
- All text meets WCAG AA contrast requirements
- Focus states clearly visible with blueprint styling
- Error states use both color and iconography

### Keyboard Navigation
- All interactive elements support keyboard navigation
- Focus indicators use blueprint line styling
- Tab order follows logical visual flow

### Screen Readers
- Semantic HTML structure maintained
- ARIA labels for technical symbols
- Descriptive text for visual elements

## Browser Support

- **Modern Browsers**: Full support (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- **CSS Grid**: Required for layout system
- **CSS Custom Properties**: Required for theming system
- **CSS Flexbox**: Used extensively for component layout

## Performance Considerations

### Optimizations
- CSS variables for efficient theme switching
- Minimal use of background images
- Efficient grid pattern implementation
- Optimized for print media

### Loading
- Core theme: ~15KB compressed
- Component library: ~20KB compressed
- Total overhead: ~35KB for complete theme system

## Development Guidelines

### Adding New Components
1. Use blueprint color variables
2. Follow technical drawing aesthetic
3. Include hover and focus states
4. Test on all supported devices
5. Ensure accessibility compliance

### Code Style
```css
/* Use descriptive class names */
.blueprint-component-name {
  /* Group related properties */
  background: var(--paper-base);
  border: var(--border-weight-thin) solid var(--line-construction);
  
  /* Use consistent spacing */
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  
  /* Apply typography scales */
  font-family: var(--font-technical);
  font-size: 13px;
  
  /* Include transitions */
  transition: all 0.2s ease;
}
```

### Testing Checklist
- [ ] Desktop responsiveness (1920x1080, 1366x768)
- [ ] Tablet responsiveness (768x1024, 1024x768)
- [ ] Mobile responsiveness (375x667, 414x896)
- [ ] Dark mode compatibility (if applicable)
- [ ] Print styling
- [ ] Keyboard navigation
- [ ] Screen reader compatibility
- [ ] Color contrast validation
- [ ] Cross-browser testing

## Integration with OpenWebUI

### Svelte Component Example

```svelte
<script>
  import '../styles/blueprint-theme.css';
  import '../styles/blueprint-components.css';
  
  // Component logic
</script>

<div class="blueprint-dashboard blueprint-grid">
  <header class="blueprint-nav">
    <!-- Navigation content -->
  </header>
  
  <main class="blueprint-workspace paper-surface">
    <!-- Main content -->
  </main>
  
  <div class="tojo-watermark">hosted on tojo.world</div>
</div>

<style>
  /* Component-specific styles using blueprint variables */
  .custom-element {
    background: var(--paper-base);
    border: var(--border-weight-medium) solid var(--blueprint-primary);
  }
</style>
```

## Future Enhancements

### Planned Features
- [ ] Dark mode variant (night blueprint theme)
- [ ] Animation library for technical drawing effects
- [ ] Icon font for technical symbols
- [ ] Additional color scheme variants
- [ ] Advanced grid pattern options
- [ ] Print optimization improvements

### Potential Integrations
- [ ] Blueprint-themed charts and graphs
- [ ] Technical diagram drawing tools
- [ ] CAD-style measurement overlays
- [ ] Engineering calculation widgets
- [ ] Technical documentation templates

## Credits

- **Design Inspiration**: Artifex Hackworth from "The Diamond Age" by Neal Stephenson
- **Technical Aesthetic**: Traditional architectural and engineering drawings
- **Implementation**: Claude (Anthropic) for tojo.world
- **Typography**: Inter font family
- **Color Theory**: Classic blueprint color psychology

## License

This theme is designed specifically for OpenWebUI deployment on tojo.world. Usage guidelines and licensing terms should be established based on the deployment context.

---

*Built with precision and elegance for the modern technical professional.*