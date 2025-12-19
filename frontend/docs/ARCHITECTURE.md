# React Frontend Architecture

## Overview
React + TypeScript + Vite frontend with shadcn/ui components for RAG chat interface. Built with modern tooling for fast development and optimized production builds.

## Core Technologies

### 1. **Vite Build Tool**
- **Purpose:** Lightning-fast development server and production build tool
- **Dev Server Port:** 5173
- **Production:** Served via Spring Boot 8080
- **Config File:** `vite.config.ts`
- **Benefits:** Fast HMR, optimized bundling, minimal configuration

### 2. **React 18.x**
- **Purpose:** UI framework for building interactive components
- **Entry Point:** `src/main.tsx`
- **Root Component:** `src/App.tsx`
- **Hooks:** Used for state management and side effects

### 3. **TypeScript**
- **Purpose:** Type-safe JavaScript for better code quality
- **Config:** `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`
- **Benefits:** Compile-time type checking, better IDE support

### 4. **Tailwind CSS**
- **Purpose:** Utility-first CSS framework for styling
- **Config:** `tailwind.config.ts`
- **PostCSS:** `postcss.config.js` for CSS processing
- **Benefits:** Rapid UI development, consistent styling

### 5. **shadcn/ui**
- **Purpose:** Pre-built, accessible Radix UI components styled with Tailwind
- **Components:** Buttons, input fields, cards, dialogs, etc.
- **Accessibility:** Built-in ARIA attributes and keyboard navigation
- **Customizable:** Components can be extended and modified

## Data Flow

```
User Types Query in Chat Interface
    ↓
React Component State Updates (useState)
    ↓
ChatService.sendQuery(message)  [HTTP POST]
    ↓
Spring Boot Backend (8080)
    ↓
Python RAG Service (11435)
    ↓
Response JSON Received
    ↓
Update Component State with Response
    ↓
UI Re-renders to Display Answer
```

## Project Structure

```
frontend/
├── src/
│   ├── components/              # Reusable UI components
│   │   ├── NavLink.tsx
│   │   └── ui/                  # shadcn/ui components
│   │
│   ├── pages/                   # Page-level components
│   │   ├── Index.tsx            # Home/Chat page
│   │   └── NotFound.tsx         # 404 page
│   │
│   ├── services/                # API communication
│   │   └── chatApi.ts           # RAG service API calls
│   │
│   ├── types/                   # TypeScript interfaces
│   │   └── chat.ts              # Chat-related types
│   │
│   ├── hooks/                   # Custom React hooks
│   │   ├── use-mobile.tsx
│   │   ├── use-toast.ts
│   │   └── useChatMessages.ts   # Chat state management
│   │
│   ├── lib/                     # Utility functions
│   │   └── utils.ts
│   │
│   ├── App.tsx                  # Root component
│   ├── App.css
│   ├── main.tsx                 # Entry point
│   ├── index.css                # Global styles
│   └── vite-env.d.ts            # Vite type declarations
│
├── public/                       # Static assets
│   └── robots.txt
│
├── index.html                    # HTML template
├── vite.config.ts               # Vite configuration
├── tsconfig.json                # TypeScript config
├── tailwind.config.ts           # Tailwind CSS config
├── postcss.config.js            # PostCSS config
├── eslint.config.js             # ESLint config
├── components.json              # shadcn/ui config
├── package.json                 # Dependencies & scripts
└── bun.lockb                    # Dependency lock file
```

## Component Hierarchy

```
App (Root)
├── Navigation/Header
├── Chat Interface
│   ├── Message List
│   │   ├── User Message
│   │   └── Assistant Message
│   └── Input Form
│       └── Send Button
└── Footer (optional)
```

## Key Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| react | 18.x | UI framework |
| typescript | Latest | Type safety |
| vite | Latest | Build tool |
| tailwindcss | Latest | Styling |
| shadcn/ui | Latest | UI components |
| axios or fetch | Latest | HTTP requests |

## Build & Run

### Development
```bash
npm install
npm run dev
```
Starts dev server on `http://localhost:5173`

### Production Build
```bash
npm run build
```
Creates optimized build in `dist/` folder

### Preview Production Build
```bash
npm run preview
```

## Environment Configuration

Create `.env.local` for environment variables:
```
VITE_API_URL=http://localhost:8080
VITE_RAG_ENDPOINT=/api/rag/chat
```

Access in code:
```typescript
const apiUrl = import.meta.env.VITE_API_URL;
```
