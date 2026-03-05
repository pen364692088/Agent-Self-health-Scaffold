---
name: anthropic-frontend-design
description: Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Combines the design intelligence of UI/UX Pro Max with Anthropic's anti-slop philosophy. Use for building UI components, pages, applications, or interfaces with exceptional attention to detail and bold creative choices.
metadata:
  clawdbot:
    emoji: "🎨"
---

# Anthropic Frontend Design

**Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics.**

This skill combines advanced design intelligence with Anthropic's anti-slop philosophy to create interfaces that are both beautiful and meaningful.

## Core Philosophy

### Anti-Slop Design
- Reject generic, templated solutions
- Embrace bold, distinctive creative choices
- Prioritize user experience over trends
- Create interfaces with personality and purpose

### Production-Grade Quality
- Industry best practices and standards
- Accessibility and inclusivity built-in
- Performance optimized implementations
- Maintainable and scalable code architecture

## Design Principles

### 🎯 Purpose-Driven Design
- Every element serves a clear function
- Visual hierarchy supports user goals
- Interaction design enhances usability
- Aesthetic choices reinforce brand identity

### 🚫 Anti-Slop Guidelines
- No generic gradients or shadows
- Avoid clichéd iconography and layouts
- Reject cookie-cutter component libraries
- Create unique visual language

### ✨ Exceptional Attention to Detail
- Micro-interactions and animations
- Consistent spacing and typography
- Thoughtful color palettes and contrast
- Delightful user experience moments

## Usage

```bash
# Design a complete application
anthropic-design create "task management app" --style "minimalist-bold"

# Create specific components
anthropic-design component "data-table" --features ["sorting", "filtering", "export"]

# Design system development
anthropic-design system --brand "tech-startup" --principles ["clarity", "efficiency", "innovation"]

# Interface critique and improvement
anthropic-design critique "./existing-ui" --focus "usability" --recommendations
```

## Design Patterns

### Layout Systems
```css
/* Custom grid system - not Bootstrap */
.grid-custom {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: calc(var(--spacing) * 1.5);
  max-width: 1400px;
  margin: 0 auto;
}
```

### Typography Hierarchy
```css
/* Distinctive typography scale */
.text-hero {
  font-size: clamp(2.5rem, 8vw, 4rem);
  font-weight: 300;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.text-body {
  font-size: 1.125rem;
  line-height: 1.7;
  font-weight: 400;
}
```

### Color Systems
```css
/* Unique color palette */
:root {
  --primary: #1a1a2e;
  --accent: #f39c12;
  --surface: #f8f9fa;
  --text: #2c3e50;
  --subtle: #95a5a6;
}
```

## Component Library

### Navigation
- Custom header designs
- Innovative menu patterns
- Context-aware navigation
- Mobile-first responsive design

### Data Display
- Distinctive table designs
- Custom chart components
- Interactive data visualizations
- Progressive disclosure patterns

### Forms
- Intuitive input designs
- Smart validation patterns
- Progressive enhancement
- Accessibility-first approach

## Design System Features

### Custom Components
```javascript
// Unique button design
const BoldButton = ({ variant = 'primary', size = 'medium', children }) => (
  <button 
    className={`btn btn-${variant} btn-${size}`}
    style={{
      borderRadius: '2px',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
    }}
  >
    {children}
  </button>
);
```

### Animation System
```css
/* Purposeful animations */
@keyframes slideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

## Configuration

```yaml
anthropic_design:
  # Design principles
  principles: ["clarity", "boldness", "purpose", "innovation"]
  
  # Technical preferences
  framework: "react"
  styling: "css-in-js"
  accessibility: "wcag-2.1-aa"
  
  # Brand customization
  brand_colors:
    primary: "#1a1a2e"
    accent: "#f39c12"
    neutral: "#95a5a6"
  
  # Typography
  font_families:
    heading: "Inter, system-ui, sans-serif"
    body: "Inter, system-ui, sans-serif"
    mono: "JetBrains Mono, monospace"
```

## Anti-Slop Detection

The skill includes built-in detection for common design slop:
- Generic gradient backgrounds
- Overused shadow effects
- Clichéd icon libraries
- Template-based layouts
- Bootstrap-style components

## Quality Assurance

### Design Review Checklist
- [ ] Unique visual identity
- [ ] Consistent design language
- [ ] Accessibility compliance
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility
- [ ] User experience testing

### Code Quality Standards
- Semantic HTML structure
- CSS organization and maintainability
- JavaScript best practices
- Performance optimization
- SEO considerations

## Integration

### Design Tools
- Figma integration
- Design token synchronization
- Component library generation
- Style guide automation

### Development Workflow
- Design-to-code pipeline
- Component documentation
- Storybook integration
- Design system maintenance

## Best Practices

1. **Start with Purpose**: Define user goals before design
2. **Embrace Constraints**: Use limitations as creative opportunities
3. **Iterate Relentlessly**: Refine based on user feedback
4. **Document Decisions**: Maintain design rationale and guidelines
5. **Test Thoroughly**: Validate with real users and scenarios

## Examples

### Dashboard Design
- Clean data visualization
- Intuitive navigation
- Responsive layouts
- Performance optimization

### E-commerce Interface
- Product showcase innovation
- Streamlined checkout process
- Mobile-first design
- Conversion optimization

### SaaS Application
- Complex data management
- User onboarding flows
- Feature discovery
- Retention-focused design

Anthropic Frontend Design helps you create interfaces that stand out, delight users, and avoid the generic aesthetics that plague many AI-generated designs.