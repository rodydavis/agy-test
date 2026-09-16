# agy-test

> High-performance 3D WebGL landing page built with **Astro 5** and **Three.js**, engineered for extreme speed, accessibility, and zero-JS initial paint.

[![Astro](https://img.shields.io/badge/Astro-5.4-FF5D01.svg?logo=astro&logoColor=white)](https://astro.build)
[![Three.js](https://img.shields.io/badge/Three.js-0.174-black.svg?logo=threedotjs&logoColor=white)](https://threejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Table of Contents

- [Overview & Architecture](#overview--architecture)
  - [Zero-JS Initial Paint](#zero-js-initial-paint)
  - [Dynamic Idle Hydration](#dynamic-idle-hydration)
  - [Zero Framework Wrapper Tax](#zero-framework-wrapper-tax)
- [Procedural 3D WebGL Features](#procedural-3d-webgl-features)
  - [Torus Knot Centerpiece](#torus-knot-centerpiece)
  - [Inner Glowing Core](#inner-glowing-core)
  - [Particle Constellation](#particle-constellation)
  - [Inertial Pointer Parallax](#inertial-pointer-parallax)
- [Performance & Battery Optimizations](#performance--battery-optimizations)
  - [Viewport Culling with IntersectionObserver](#viewport-culling-with-intersectionobserver)
  - [Tab Visibility Lifecycle](#tab-visibility-lifecycle)
  - [Device Pixel Ratio (DPR) Clamping](#device-pixel-ratio-dpr-clamping)
  - [Zero External Asset Overhead](#zero-external-asset-overhead)
  - [Lifecycle Teardown & Context Disposal](#lifecycle-teardown--context-disposal)
- [Accessibility & User Experience](#accessibility--user-experience)
  - [prefers-reduced-motion Support](#prefers-reduced-motion-support)
  - [Screen Reader Accessibility](#screen-reader-accessibility)
  - [Live Engine Status Telemetry](#live-engine-status-telemetry)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Development](#development)
  - [Production Build](#production-build)
  - [Preview](#preview)

---

## Overview & Architecture

Modern landing pages frequently suffer from severe performance penalties when integrating 3D graphics: massive bundle payloads, delayed First Contentful Paint (FCP), blocked main threads, and persistent battery drain. 

This project demonstrates a production-grade architecture combining **Astro 5's Islands Architecture** with an isolated **Three.js WebGL canvas** that eliminates these drawbacks.

```
┌─────────────────────────────────────────────────────────────┐
│                    SSR HTML Initial Paint                   │
│         (Pre-rendered semantic DOM, CSS background)         │
│                 FCP < 300ms • Zero JS blocked               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             requestIdleCallback / DOMContentLoaded           │
│          Dynamic import('three') loaded during idle         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Interactive WebGL Hero Engine                 │
│    Active 60 FPS ◄───► Standby GPU Idle (Intersection)      │
└─────────────────────────────────────────────────────────────┘
```

### Zero-JS Initial Paint
The entire hero layout—typography, action buttons, status pill, and responsive gradients—is pre-rendered as static HTML by Astro. Visitors receive immediate content without waiting for JavaScript bundles or 3D engine evaluation.

### Dynamic Idle Hydration
Three.js is loaded dynamically via dynamic `import('three')` inside a `requestIdleCallback` (with fallback timeout) scheduler. This guarantees that critical resources and user interactions take priority before 3D initialization begins.

### Zero Framework Wrapper Tax
Instead of heavy component wrappers or virtual-DOM reconciliation layers, Three.js runs directly against the `<canvas>` element in an Astro client script. This guarantees maximum rendering throughput and low memory overhead.

---

## Procedural 3D WebGL Features

All scene assets are generated algorithmically at runtime, eliminating 3D model downloads:

| Feature | Technical Specification | Description |
| :--- | :--- | :--- |
| **Glowing Centerpiece** | `TorusKnotGeometry(1.5, 0.42, 128, 32)` | Indigo wireframe mesh (`#6366f1`) with standard material roughness, 85% metalness, and emissive glow. |
| **Inner Core** | `IcosahedronGeometry(0.85, 2)` | Sky blue wireframe sphere (`#38bdf8`) rotating counter to the outer torus knot. |
| **Constellation** | 1,500 Star Particles (`BufferGeometry`) | Dynamic float buffer with tri-color vertex palette (indigo, sky blue, purple) rendered with additive blending. |
| **Pointer Parallax** | Inertial Lerp Smoothing | Tracks cursor coordinates with gentle easing (`0.05` lerp) affecting hero group rotation, constellation tilt, and camera offset. |
| **Dual Point Lighting** | Indigo (`0x6366f1`) & Sky (`0x38bdf8`) | Balanced ambient illumination (0.7 intensity) complemented by opposing point lights for depth and specular highlights. |

---

## Performance & Battery Optimizations

To ensure the 3D scene does not consume unnecessary system resources or drain device batteries, several optimization strategies are implemented:

### Viewport Culling with IntersectionObserver
An `IntersectionObserver` monitors the hero container:
- When the hero scrolls out of view, `cancelAnimationFrame` immediately halts the render loop.
- The engine status transitions to `Standby (GPU Idle)`.
- When scrolled back into view, the render loop seamlessly resumes.

### Tab Visibility Lifecycle
A `visibilitychange` listener pauses rendering immediately when the user switches browser tabs or minimizes the window, ensuring zero background CPU/GPU consumption.

### Device Pixel Ratio (DPR) Clamping
High-density displays (such as 3x Retina screens) can place exponential fill-rate demands on mobile GPUs. The renderer clamps pixel density:
```typescript
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
```

### Zero External Asset Overhead
Because all geometries, materials, and star fields are procedural:
- **0 KB** external `.gltf`, `.glb`, or `.obj` assets downloaded.
- **0 external network requests** for 3D textures or models.

### Lifecycle Teardown & Context Disposal
To support view transitions or single-page navigation without memory leaks, full cleanup logic is wired to `astro:before-swap` and `beforeunload`:
- Disposes geometries, materials, and point systems.
- Calls `renderer.dispose()` and forces context release with `renderer.forceContextLoss()`.
- Disconnects all observers and deregisters event listeners.

---

## Accessibility & User Experience

Accessible WebGL is a core requirement of this implementation:

- **`prefers-reduced-motion` Compliance**: The engine listens to `(prefers-reduced-motion: reduce)`. If enabled, animation loops are halted, the scene renders a single static composition, and status reflects `Static (Reduced Motion)`.
- **Screen Reader Accessibility**: The canvas element is explicitly hidden from assistive technology with `aria-hidden="true"`. All informative hero titles, descriptions, and call-to-actions reside in accessible semantic HTML.
- **Live Engine Telemetry**: A live region pill (`aria-live="polite"`) displays the engine's current state:
  - 🟢 **Active (60 FPS)**: WebGL loop running normally.
  - 🟡 **Standby (GPU Idle)**: Paused via IntersectionObserver or tab backgrounding.
  - 🔵 **Static (Reduced Motion)**: User prefers reduced motion.
  - ⚪ **CSS Fallback Mode**: Graceful degradation if WebGL is unavailable.

---

## Project Structure

```
agy-test/
├── public/
│   └── favicon.svg              # Favicon asset
├── src/
│   ├── components/
│   │   └── ThreeHero.astro      # WebGL scene, lifecycle management, and canvas container
│   ├── layouts/
│   │   └── Layout.astro         # HTML skeleton, design tokens, and global CSS variables
│   └── pages/
│       └── index.astro          # Landing page layout, hero content, feature grid, and specs
├── astro.config.mjs             # Astro project configuration
├── package.json                 # Project dependencies and script commands
├── tsconfig.json                # TypeScript compiler configuration
└── README.md                    # Project documentation
```

### Key Components

- **[`ThreeHero.astro`](src/components/ThreeHero.astro)**: Encapsulates the `<canvas>` element, dynamic Three.js loading, scene setup, lighting, procedural meshes, particle system, parallax interaction, observer hooks, and resource teardown.
- **[`Layout.astro`](src/layouts/Layout.astro)**: Defines global CSS design tokens (colors, font stack, focus ring styling), standard document meta tags, and responsive viewport sizing.
- **[`index.astro`](src/pages/index.astro)**: Assembles the landing page, combining the dynamic hero component with semantic HTML sections detailing architecture, capabilities, and key project metrics.

---

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) `v18.17.1` or higher
- [npm](https://www.npmjs.com/) (bundled with Node.js)

### Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/rodydavis/agy-test.git
cd agy-test
npm install
```

### Development

Launch the local development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

The application will be accessible at `http://localhost:4321`.

### Production Build

Compile the static production build to `dist/`:

```bash
npm run build
```

### Preview

Locally serve the production build before deployment:

```bash
npm run preview
```