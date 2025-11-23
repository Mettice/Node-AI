# Phase 0: Foundation & Setup

**Duration:** Week 1  
**Status:** 🔄 Not Started

---

## 🎯 Goals

- Set up project structure
- Configure development environment
- Establish coding standards
- Create basic documentation

---

## 📋 Tasks

### Backend Setup

#### 1. Project Structure
- [ ] Create `backend/` directory with all subdirectories:
  ```
  backend/
  ├── core/
  ├── nodes/
  │   ├── input/
  │   ├── processing/
  │   ├── embedding/
  │   ├── storage/
  │   ├── retrieval/
  │   └── llm/
  ├── api/
  ├── services/
  ├── storage/
  ├── utils/
  └── tests/
  ```
- [ ] Initialize Python virtual environment
- [ ] Create `requirements.txt` with core dependencies:
  - FastAPI 0.109+
  - Pydantic 2.5+
  - Uvicorn 0.27+
  - OpenAI SDK 1.10+
  - tiktoken 0.5+
  - FAISS 1.7+
  - pytest 7.4+
  - python-multipart (for file uploads)
- [ ] Set up `pyproject.toml` for modern Python packaging
- [ ] Create `backend/__init__.py` files in all packages

#### 2. Development Tools
- [ ] Configure `ruff` for linting
  - Create `ruff.toml` or `pyproject.toml` section
  - Set up rules and line length
- [ ] Configure `black` for formatting
  - Create `pyproject.toml` section for black
  - Set line length to 100
- [ ] Set up `pre-commit` hooks
  - Create `.pre-commit-config.yaml`
  - Add hooks for ruff, black, and basic checks
- [ ] Create `.env.example` with all required variables:
  ```
  # API Keys
  OPENAI_API_KEY=your_openai_key_here
  
  # Server
  HOST=0.0.0.0
  PORT=8000
  DEBUG=True
  
  # CORS
  CORS_ORIGINS=http://localhost:5173,http://localhost:3000
  
  # Storage
  DATA_DIR=./data
  WORKFLOWS_DIR=./data/workflows
  EXECUTIONS_DIR=./data/executions
  VECTORS_DIR=./data/vectors
  ```

#### 3. Core Configuration
- [ ] Create `backend/config.py` with Pydantic settings:
  ```python
  from pydantic_settings import BaseSettings
  
  class Settings(BaseSettings):
      openai_api_key: str
      host: str = "0.0.0.0"
      port: int = 8000
      debug: bool = False
      cors_origins: list[str] = ["http://localhost:5173"]
      data_dir: str = "./data"
      # ... more settings
      
      class Config:
          env_file = ".env"
  ```
- [ ] Set up logging configuration
  - Create `backend/utils/logger.py`
  - Configure structured logging
  - Set log levels based on environment
- [ ] Create basic FastAPI app structure
  - Create `backend/main.py`
  - Set up CORS middleware
  - Add request logging
- [ ] Add health check endpoint
  - `GET /api/v1/health`
  - Returns API status and version

#### 4. Testing Infrastructure
- [ ] Set up `pytest` configuration
  - Create `pytest.ini` or `pyproject.toml` section
  - Configure test discovery
  - Set up async test support
- [ ] Create test directory structure:
  ```
  tests/
  ├── backend/
  │   ├── test_models.py
  │   ├── test_nodes.py
  │   ├── test_engine.py
  │   └── test_api.py
  └── conftest.py
  ```
- [ ] Add fixtures for common test scenarios
  - Mock OpenAI API responses
  - Test workflow fixtures
  - Temporary file fixtures
- [ ] Set up test database (SQLite for now)
  - Create test database helper
  - Cleanup after tests

---

### Frontend Setup

#### 1. Project Structure
- [ ] Initialize Vite + React + TypeScript project
  ```bash
  npm create vite@latest frontend -- --template react-ts
  ```
- [ ] Set up directory structure:
  ```
  frontend/src/
  ├── components/
  │   ├── Canvas/
  │   ├── Sidebar/
  │   ├── Properties/
  │   └── Execution/
  ├── hooks/
  ├── services/
  ├── store/
  ├── types/
  ├── utils/
  └── styles/
  ```
- [ ] Configure Tailwind CSS
  - Install Tailwind CSS
  - Create `tailwind.config.js`
  - Set up `index.css` with Tailwind directives
- [ ] Set up React Flow
  - Install `reactflow`
  - Create basic canvas component
  - Configure React Flow styles

#### 2. Development Tools
- [ ] Configure ESLint
  - Create `.eslintrc.cjs` or use Vite defaults
  - Add React and TypeScript rules
- [ ] Configure Prettier
  - Create `.prettierrc`
  - Set up formatting rules
- [ ] Set up Vite plugins
  - Configure path aliases (`@/` for src)
  - Set up environment variables
- [ ] Create `.env.example` for frontend:
  ```
  VITE_API_URL=http://localhost:8000
  VITE_APP_NAME=RAGFlow
  ```

#### 3. State Management
- [ ] Set up Zustand store structure
  - Install Zustand
  - Create `frontend/src/store/workflowStore.ts`
  - Define store interface
- [ ] Create base types for workflow, nodes, edges
  - Create `frontend/src/types/workflow.ts`
  - Create `frontend/src/types/node.ts`
  - Create `frontend/src/types/execution.ts`
- [ ] Set up TanStack Query for API calls
  - Install `@tanstack/react-query`
  - Create query client
  - Set up providers

#### 4. UI Foundation
- [ ] Create basic layout components:
  - `App.tsx` - Main app component
  - `Layout.tsx` - Main layout with header, sidebar, canvas, properties
  - `Header.tsx` - Top navigation bar
- [ ] Set up routing (if needed)
  - Install React Router (optional for MVP)
- [ ] Create theme configuration
  - Define color palette
  - Set up CSS variables
  - Create theme provider
- [ ] Add basic styling system
  - Create utility classes
  - Set up component styles
  - Add responsive breakpoints

---

### Documentation

#### 1. Project Documentation
- [ ] Create `README.md` with:
  - Project description
  - Quick start guide
  - Installation instructions
  - Development setup
  - Environment variables
  - Running the project
- [ ] Create `CONTRIBUTING.md` with:
  - Development guidelines
  - Code style guide
  - Git workflow
  - Testing requirements
  - Pull request process
- [ ] Document environment variables
  - List all required variables
  - Explain each variable
  - Provide examples
- [ ] Create architecture diagram
  - System architecture overview
  - Component relationships
  - Data flow diagram

#### 2. Code Documentation
- [ ] Set up docstring standards
- [ ] Add type hints to all functions
- [ ] Document module purposes

---

## ✅ Deliverables Checklist

- [ ] Project structure created
- [ ] Development environment working
- [ ] Both backend and frontend can start
- [ ] Backend health check endpoint works
- [ ] Frontend can connect to backend
- [ ] Linting/formatting configured
- [ ] Pre-commit hooks working
- [ ] Test infrastructure set up
- [ ] Basic documentation complete

---

## 🧪 Verification Steps

1. **Backend Verification:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn main:app --reload
   # Visit http://localhost:8000/api/v1/health
   ```

2. **Frontend Verification:**
   ```bash
   cd frontend
   npm install
   npm run dev
   # Visit http://localhost:5173
   ```

3. **Linting Verification:**
   ```bash
   # Backend
   ruff check backend/
   black --check backend/
   
   # Frontend
   npm run lint
   ```

4. **Testing Verification:**
   ```bash
   # Backend
   pytest tests/
   ```

---

## 📝 Notes

- Keep dependencies minimal for MVP
- Use environment variables for all configuration
- Set up proper error handling from the start
- Document as you go, not at the end
- Test infrastructure early to catch issues

---

## 🔗 Related Files

- `backend/main.py` - FastAPI application entry point
- `backend/config.py` - Configuration settings
- `frontend/src/App.tsx` - React application entry point
- `.env.example` - Environment variables template
- `README.md` - Project documentation

---

## ➡️ Next Phase

Once Phase 0 is complete, proceed to [Phase 1: Core Engine & First Nodes](./PHASE_1_CORE_ENGINE.md)

