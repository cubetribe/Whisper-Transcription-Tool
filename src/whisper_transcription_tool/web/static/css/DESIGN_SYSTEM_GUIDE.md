# Whisper Transcription Tool - Design System Guide

## Overview

Dieses Design System basiert auf der professionellen Phone Recording Seite und stellt einheitliche Design-Standards für alle Seiten bereit.

## Design Philosophy

- **Desktop-First**: Optimiert für Desktop-Anwendungen (1200px+)
- **Professional**: Clean, moderne Aesthetik
- **Consistent**: Einheitliche Komponenten und Patterns
- **Accessible**: WCAG 2.1 AA konform
- **Performance**: Optimiert für schnelle Ladezeiten

## Quick Start

```html
<!-- Include Design System -->
<link rel="stylesheet" href="{{ url_for('static', path='/css/design_system.css') }}">

<!-- Basic Page Structure -->
<div class="container">
    <header class="header-section">
        <h1><i class="fas fa-icon"></i> Page Title</h1>
        <div class="status-indicator online">
            <i class="fas fa-circle"></i> Online
        </div>
    </header>

    <div class="card">
        <div class="card-header">
            <h2 class="card-title"><i class="fas fa-cog"></i> Section Title</h2>
        </div>
        <p>Content here...</p>
        <button class="btn btn-primary">
            <i class="fas fa-play"></i> Action
        </button>
    </div>
</div>
```

## Design Tokens

### Colors

```css
/* Primary Colors */
--primary-color: #2563eb
--primary-hover: #1d4ed8
--primary-light: #dbeafe

/* Semantic Colors */
--success-color: #10b981
--warning-color: #f59e0b
--danger-color: #ef4444
--info-color: #06b6d4

/* Neutral Colors */
--dark-color: #1e293b
--text-color: #334155
--text-muted: #64748b
--background-color: #ffffff
--light-background: #f8fafc
--border-color: #e2e8f0
```

### Typography

```css
/* Font Sizes */
--font-size-xs: 0.75rem    /* 12px */
--font-size-sm: 0.875rem   /* 14px */
--font-size-base: 1rem     /* 16px */
--font-size-lg: 1.125rem   /* 18px */
--font-size-xl: 1.25rem    /* 20px */
--font-size-2xl: 1.5rem    /* 24px */
--font-size-3xl: 1.875rem  /* 30px */

/* Font Weights */
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700
```

### Spacing (8px Grid System)

```css
--space-1: 0.25rem  /* 4px */
--space-2: 0.5rem   /* 8px */
--space-3: 0.75rem  /* 12px */
--space-4: 1rem     /* 16px */
--space-5: 1.25rem  /* 20px */
--space-6: 1.5rem   /* 24px */
--space-8: 2rem     /* 32px */
--space-10: 2.5rem  /* 40px */
```

## Component Library

### Buttons

```html
<!-- Primary Actions -->
<button class="btn btn-primary">
    <i class="fas fa-play"></i> Start
</button>

<!-- Secondary Actions -->
<button class="btn btn-secondary">Cancel</button>

<!-- Status Buttons -->
<button class="btn btn-success">Save</button>
<button class="btn btn-warning">Pause</button>
<button class="btn btn-danger">Stop</button>
<button class="btn btn-info">Info</button>

<!-- Button Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Normal</button>
<button class="btn btn-primary btn-lg">Large</button>

<!-- Button Variants -->
<button class="btn btn-outline">Outline</button>
<button class="btn btn-ghost">Ghost</button>
```

### Cards

```html
<!-- Basic Card -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">
            <i class="fas fa-cog"></i> Card Title
        </h3>
    </div>
    <p>Card content here...</p>
</div>

<!-- Card Variants -->
<div class="card card-compact">Compact padding</div>
<div class="card card-spacious">Spacious padding</div>
```

### Status Indicators

```html
<!-- Status Indicators -->
<span class="status-indicator online">
    <i class="fas fa-circle"></i> Online
</span>
<span class="status-indicator offline">
    <i class="fas fa-circle"></i> Offline
</span>
<span class="status-indicator warning">
    <i class="fas fa-exclamation-triangle"></i> Warning
</span>

<!-- Status Grid -->
<div class="status-grid">
    <div class="status-item">
        <span class="label">Service:</span>
        <span class="value available">Available</span>
    </div>
    <div class="status-item">
        <span class="label">Status:</span>
        <span class="value unavailable">Unavailable</span>
    </div>
</div>
```

### Forms

```html
<div class="form-group">
    <label class="form-label">Input Label</label>
    <input type="text" class="form-input" placeholder="Enter text...">
</div>

<div class="form-group">
    <label class="form-label">Select Option</label>
    <select class="form-select">
        <option>Option 1</option>
        <option>Option 2</option>
    </select>
</div>

<div class="form-group">
    <label class="form-label">Textarea</label>
    <textarea class="form-textarea" rows="4"></textarea>
</div>
```

### Progress Bars

```html
<div class="progress-container">
    <div class="progress-bar">
        <div class="progress-fill" style="width: 45%"></div>
    </div>
    <span class="progress-text">Processing... 45%</span>
</div>

<!-- Audio Level Meters -->
<div class="level-meter">
    <label class="form-label">Audio Level:</label>
    <div class="meter-container">
        <div class="meter-bar">
            <div class="meter-fill" style="width: 75%"></div>
        </div>
        <span>75%</span>
    </div>
</div>
```

### Notifications

```html
<!-- Success Notification -->
<div class="notification success">
    <i class="fas fa-check-circle"></i>
    Operation completed successfully!
</div>

<!-- Error Notification -->
<div class="notification error">
    <i class="fas fa-exclamation-circle"></i>
    An error occurred!
</div>
```

## Layout System

### Grid System

```html
<div class="grid grid-2">
    <div>Column 1</div>
    <div>Column 2</div>
</div>

<div class="grid grid-3">
    <div>Column 1</div>
    <div>Column 2</div>
    <div>Column 3</div>
</div>

<div class="grid grid-auto">
    <!-- Auto-fit columns -->
</div>
```

### Flexbox Utilities

```html
<div class="flex items-center justify-between gap-4">
    <div>Left content</div>
    <div>Right content</div>
</div>

<div class="flex flex-col gap-6">
    <div>Item 1</div>
    <div>Item 2</div>
</div>
```

## Typography Classes

```html
<!-- Text Sizes -->
<p class="text-xs">Extra small text</p>
<p class="text-sm">Small text</p>
<p class="text-base">Base text</p>
<p class="text-lg">Large text</p>
<p class="text-xl">Extra large text</p>

<!-- Text Colors -->
<p class="text-primary">Primary color</p>
<p class="text-success">Success color</p>
<p class="text-warning">Warning color</p>
<p class="text-danger">Danger color</p>
<p class="text-muted">Muted text</p>

<!-- Font Weights -->
<p class="font-normal">Normal weight</p>
<p class="font-medium">Medium weight</p>
<p class="font-semibold">Semibold weight</p>
<p class="font-bold">Bold weight</p>
```

## Utility Classes

### Spacing

```html
<!-- Margins -->
<div class="m-4">All margins</div>
<div class="mt-4">Top margin</div>
<div class="mb-4">Bottom margin</div>

<!-- Paddings -->
<div class="p-4">All padding</div>
<div class="pt-4">Top padding</div>
<div class="pb-4">Bottom padding</div>
```

### Display

```html
<div class="hidden">Hidden element</div>
<div class="block">Block element</div>
<div class="flex">Flex container</div>
```

## Animations

```html
<!-- Animation Classes -->
<div class="fade-in">Fade in animation</div>
<div class="slide-up">Slide up animation</div>
<div class="bounce">Bounce animation</div>

<!-- Loading Spinners -->
<i class="fas fa-spinner fa-spin"></i>
<i class="fas fa-circle-notch fa-pulse"></i>
```

## Responsive Design

Das System ist Desktop-first mit folgenden Breakpoints:

```css
/* Large screens: 1200px+ (default) */
/* Medium screens: 768px - 1199px */
@media (max-width: 1200px) { ... }

/* Small screens: 480px - 767px */
@media (max-width: 768px) { ... }

/* Extra small screens: < 480px */
@media (max-width: 480px) { ... }
```

## Dark Mode

Das System unterstützt automatischen Dark Mode:

```css
@media (prefers-color-scheme: dark) {
    /* Dark mode variables automatically applied */
}
```

## Best Practices

### 1. Component Structure
```html
<!-- Good -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title"><i class="fas fa-icon"></i> Title</h3>
    </div>
    <div class="card-content">
        <!-- Content -->
    </div>
</div>
```

### 2. Button Usage
```html
<!-- Primary actions -->
<button class="btn btn-primary">Save</button>

<!-- Secondary actions -->
<button class="btn btn-secondary">Cancel</button>

<!-- Destructive actions -->
<button class="btn btn-danger">Delete</button>
```

### 3. Status Communication
```html
<!-- Clear status indicators -->
<div class="status-indicator success">
    <i class="fas fa-check-circle"></i> Connected
</div>
```

### 4. Form Layout
```html
<!-- Consistent form structure -->
<div class="form-group">
    <label class="form-label">Label</label>
    <input class="form-input" type="text">
</div>
```

## Migration from Old Styles

### Button Migration
```html
<!-- Old -->
<button class="button primary">Action</button>

<!-- New -->
<button class="btn btn-primary">Action</button>
```

### Card Migration
```html
<!-- Old -->
<div class="feature-card">...</div>

<!-- New -->
<div class="card">
    <div class="card-header">
        <h3 class="card-title">...</h3>
    </div>
    ...
</div>
```

## Performance Notes

- CSS ist optimiert für minimale Reflows
- Verwendet hardware-beschleunigte Transformationen
- Efficient CSS-Variablen System
- Minimale Bundle-Größe durch systematische Struktur

## Browser Support

- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

## Customization

Um das Design System zu erweitern, füge neue CSS-Variablen in `design_system.css` hinzu:

```css
:root {
    /* Custom colors */
    --brand-primary: #your-color;
    --brand-secondary: #your-color;
}
```

## Support

Bei Fragen zum Design System oder für neue Component-Requests, siehe die Entwicklungs-Guidelines im Projekt.