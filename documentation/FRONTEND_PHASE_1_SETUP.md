# Frontend Phase 1: Setup & Foundation

**Duration:** 1-2 days  
**Status:** 📋 Not Started  
**Prerequisites:** Backend API running and tested

---

## 🎯 Goals

- Set up React + TypeScript + Vite project
- Configure build tools and dependencies
- Set up project structure
- Create base components and utilities
- Connect to backend API

---

## 📋 Tasks

### 1. Project Initialization

#### 1.1 Create Frontend Project

- [ ] Initialize Vite + React + TypeScript project
  ```bash
  npm create vite@latest frontend -- --template react-ts
  cd frontend
  npm install
  ```

- [ ] Install core dependencies
  ```bash
  npm install react react-dom
  npm install -D typescript @types/react @types/react-dom
  ```

- [ ] Install UI/UX libraries
  ```bash
  npm install reactflow zustand @tanstack/react-query
  npm install tailwindcss postcss autoprefixer
  npm install lucide-react react-hot-toast
  ```

- [ ] Install form/validation libraries
  ```bash
  npm install react-hook-form @hookform/resolvers zod
  ```

- [ ] Install HTTP client
  ```bash
  npm install axios
  # or
  npm install ky
  ```

#### 1.2 Configure Tailwind CSS

- [ ] Initialize Tailwind
  ```bash
  npx tailwindcss init -p
  ```

- [ ] Configure `tailwind.config.js`
  - Add content paths
  - Add custom colors (from design doc)
  - Add custom spacing/radius

- [ ] Create `src/index.css` with Tailwind directives
  - Base styles
  - Custom CSS variables
  - Global styles

#### 1.3 Configure TypeScript

- [ ] Set up `tsconfig.json`
  - Strict mode enabled
  - Path aliases configured
  - React JSX settings

- [ ] Configure path aliases in `vite.config.ts`
  - `@/` → `src/`
  - `@/components` → `src/components`
  - `@/utils` → `src/utils`
  - etc.

---

### 2. Project Structure

#### 2.1 Create Directory Structure

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── components/          # React components
│   │   ├── Canvas/         # Canvas-related components
│   │   ├── Sidebar/        # Sidebar components
│   │   ├── Properties/     # Properties panel components
│   │   ├── Execution/      # Execution panel components
│   │   └── common/         # Shared components
│   ├── store/              # Zustand stores
│   ├── services/           # API services
│   ├── types/              # TypeScript types
│   ├── utils/              # Utility functions
│   ├── hooks/              # Custom React hooks
│   ├── constants/          # Constants and configs
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── .env                    # Environment variables
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

#### 2.2 Create Base Files

- [ ] `src/types/workflow.ts` - Workflow types
- [ ] `src/types/node.ts` - Node types
- [ ] `src/types/api.ts` - API response types
- [ ] `src/constants/index.ts` - App constants
- [ ] `src/utils/api.ts` - API client setup
- [ ] `src/utils/errors.ts` - Error handling utilities

---

### 3. API Integration Setup

#### 3.1 Create API Client (`src/services/api.ts`)

- [ ] Set up base API client
  - Base URL from env
  - Request/response interceptors
  - Error handling
  - TypeScript types

- [ ] Create API service modules:
  - `src/services/nodes.ts` - Node-related API calls
  - `src/services/workflows.ts` - Workflow execution API
  - `src/services/executions.ts` - Execution status/trace API

#### 3.2 Environment Configuration

- [ ] Create `.env` file
  ```env
  VITE_API_URL=http://localhost:8000
  VITE_APP_NAME=NodeAI
  ```

- [ ] Create `.env.example` file
- [ ] Configure Vite to use env variables

---

### 4. State Management Setup

#### 4.1 Create Zustand Stores

- [ ] `src/store/workflowStore.ts` - Workflow state
  - Nodes array
  - Edges array
  - Selected node
  - Workflow metadata

- [ ] `src/store/executionStore.ts` - Execution state
  - Execution status
  - Execution results
  - Execution trace
  - Cost tracking

- [ ] `src/store/uiStore.ts` - UI state
  - Sidebar visibility
  - Properties panel visibility
  - Canvas zoom/pan state
  - Theme (if applicable)

---

### 5. Base Components

#### 5.1 Layout Components

- [ ] `src/components/common/Layout.tsx`
  - Main app layout
  - Header
  - Sidebar areas
  - Canvas area
  - Execution panel area

- [ ] `src/components/common/Header.tsx`
  - App title
  - User menu (placeholder)
  - Settings button (placeholder)

#### 5.2 Common UI Components

- [ ] `src/components/common/Button.tsx`
  - Variants (primary, secondary, danger)
  - Sizes (sm, md, lg)
  - Loading state
  - Disabled state

- [ ] `src/components/common/Input.tsx`
  - Text input
  - Number input
  - Textarea
  - Error states

- [ ] `src/components/common/Select.tsx`
  - Dropdown select
  - Searchable (optional)
  - Multi-select (optional)

- [ ] `src/components/common/Card.tsx`
  - Card container
  - Header/body/footer sections

- [ ] `src/components/common/Spinner.tsx`
  - Loading spinner
  - Sizes

- [ ] `src/components/common/Toast.tsx`
  - Toast notifications (using react-hot-toast)

---

### 6. Type Definitions

#### 6.1 Workflow Types (`src/types/workflow.ts`)

```typescript
export interface Node {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface Workflow {
  id?: string;
  name: string;
  nodes: Node[];
  edges: Edge[];
  metadata?: Record<string, any>;
}
```

#### 6.2 Node Types (`src/types/node.ts`)

```typescript
export interface NodeMetadata {
  type: string;
  name: string;
  description: string;
  category: string;
  config_schema: Record<string, any>;
}

export interface NodeSchema {
  type: 'object';
  properties: Record<string, any>;
  required?: string[];
}
```

#### 6.3 API Types (`src/types/api.ts`)

```typescript
export interface ExecutionResponse {
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  total_cost: number;
  duration_ms: number;
}

export interface NodeResult {
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: Record<string, any>;
  error?: string;
  cost?: number;
  duration_ms?: number;
}
```

---

### 7. Utilities

#### 7.1 API Utilities (`src/utils/api.ts`)

- [ ] Create axios instance with base config
- [ ] Request interceptor (add auth if needed)
- [ ] Response interceptor (error handling)
- [ ] Type-safe API methods

#### 7.2 Error Handling (`src/utils/errors.ts`)

- [ ] Error type definitions
- [ ] Error parsing utilities
- [ ] User-friendly error messages

#### 7.3 Node Utilities (`src/utils/nodes.ts`)

- [ ] Node category colors
- [ ] Node icons mapping
- [ ] Node validation helpers

---

### 8. App Entry Point

#### 8.1 Main App Component (`src/App.tsx`)

- [ ] Set up React Query provider
- [ ] Set up Toast provider
- [ ] Set up main layout
- [ ] Add routing (if needed for future)

#### 8.2 Entry Point (`src/main.tsx`)

- [ ] Render App component
- [ ] Import global styles

---

### 9. Testing Setup (Optional)

- [ ] Install testing libraries
  ```bash
  npm install -D vitest @testing-library/react @testing-library/jest-dom
  ```

- [ ] Configure Vitest
- [ ] Create sample test

---

## ✅ Deliverables Checklist

- [ ] Project initialized with Vite + React + TypeScript
- [ ] All dependencies installed
- [ ] Tailwind CSS configured
- [ ] TypeScript configured with path aliases
- [ ] Project structure created
- [ ] API client set up and tested
- [ ] Zustand stores created
- [ ] Base components created
- [ ] Type definitions complete
- [ ] App runs without errors
- [ ] Can connect to backend API

---

## 🧪 Testing Checklist

- [ ] App starts without errors
- [ ] Can fetch nodes from API (`/api/v1/nodes`)
- [ ] Can fetch node schema (`/api/v1/nodes/{type}`)
- [ ] Health check works (`/api/v1/health`)
- [ ] API errors are handled gracefully
- [ ] TypeScript compiles without errors

---

## 📝 Notes

- Keep it simple - we're setting up the foundation
- Don't build complex features yet
- Focus on getting the project structure right
- Test API connection early

---

## 🔗 Related Files

- `frontend/package.json` - Dependencies
- `frontend/vite.config.ts` - Vite configuration
- `frontend/tailwind.config.js` - Tailwind configuration
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/src/services/api.ts` - API client
- `frontend/src/store/workflowStore.ts` - Workflow state

---

## ➡️ Next Phase

Once Phase 1 is complete, proceed to [Frontend Phase 2: Canvas & Nodes](./FRONTEND_PHASE_2_CANVAS.md)

