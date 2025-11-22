# 🎨 NodeAI - Visual GenAI Workflow Builder

**Build, deploy, and manage AI workflows visually. No code required.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.3-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)

---

## ✨ Features

### **🎯 Visual Workflow Builder**
- Drag-and-drop canvas for building AI workflows
- Real-time execution with streaming updates
- 30+ pre-built node types
- Custom node creation support

### **🤖 AI Integrations**
- **LLM Providers**: OpenAI, Anthropic, Google Gemini, Groq
- **Multi-Agent Systems**: CrewAI for complex agent orchestration
- **RAG Workflows**: Vector stores, embeddings, retrieval, reranking
- **Hybrid RAG**: Combine vector search with knowledge graphs (Neo4j)

### **📊 Advanced Features**
- **Cost Intelligence**: Track and optimize AI spending
- **Prompt Playground**: Test and iterate on prompts
- **RAG Optimization**: Automatic parameter tuning
- **Real-time Streaming**: See your workflows execute live
- **File Processing**: PDF, DOCX, images, audio, video
- **Knowledge Bases**: Build and query knowledge repositories

### **🔐 Production-Ready Security**
- JWT authentication via Supabase
- Workflow ownership and access control
- Rate limiting on all endpoints
- File upload validation
- Error monitoring with Sentry
- CORS configuration

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Node.js 18+
- Supabase account (free tier available)

### **1. Clone Repository**

```bash
git clone https://github.com/Mettice/Node-AI.git
cd Node-AI
```

### **2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Run server
uvicorn backend.main:app --reload
```

Backend runs at: `http://localhost:8000`

### **3. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000

# Run dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### **4. Access the App**

1. Open `http://localhost:5173`
2. Register a new account
3. Verify email (check Supabase dashboard in dev)
4. Start building workflows!

---

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Deploy to production
- **[Beta Deployment Checklist](BETA_DEPLOYMENT_CHECKLIST.md)** - Pre-launch checklist
- **[Deployment Audit](DEPLOYMENT_READINESS_AUDIT.md)** - Security audit report
- **[Workflow Access Control](WORKFLOW_ACCESS_CONTROL_IMPLEMENTATION.md)** - Access control docs
- **[Rate Limiting](RATE_LIMITING_IMPLEMENTATION.md)** - API rate limiting

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         React + Vite Frontend               │
│  - Visual workflow canvas (React Flow)      │
│  - Real-time execution streaming (SSE)      │
│  - Zustand state management                 │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│        FastAPI Backend                      │
│  - Workflow execution engine                │
│  - Node registry (30+ node types)           │
│  - Streaming via Server-Sent Events         │
│  - JWT authentication                       │
└──────┬──────────────────────────────────────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
  Supabase          AI APIs           Vector DBs
  Auth/DB      (OpenAI, Claude)    (Pinecone, etc)
```

---

## 🎯 Use Cases

### **1. RAG Applications**
- Build retrieval-augmented generation workflows
- Combine multiple data sources
- Optimize with automatic parameter tuning

### **2. Multi-Agent Systems**
- Create complex agent workflows with CrewAI
- Define roles, goals, and tasks
- Orchestrate multiple AI models

### **3. Document Processing**
- Extract text from PDFs, images, audio
- Process and chunk documents
- Build searchable knowledge bases

### **4. Custom AI Pipelines**
- Chain multiple AI models
- Add conditional logic
- Integrate external APIs

---

## 🛠️ Technology Stack

### **Frontend**
- React 18.3
- TypeScript
- Vite
- React Flow (canvas)
- Zustand (state management)
- Tailwind CSS
- Lucide icons

### **Backend**
- Python 3.11+
- FastAPI
- Pydantic
- LangChain
- CrewAI
- Supabase (auth)
- Sentry (monitoring)

### **AI Integrations**
- OpenAI GPT-4, GPT-3.5
- Anthropic Claude 3
- Google Gemini
- Groq (fast inference)
- Cohere (reranking)
- Voyage AI (embeddings)

### **Vector Stores**
- Pinecone
- Chroma
- FAISS

---

## 📦 Deployment

### **Recommended Stack**

- **Frontend**: Vercel (automatic from GitHub)
- **Backend**: Railway or Render
- **Database**: Supabase (PostgreSQL + Auth)
- **Monitoring**: Sentry
- **File Storage**: Local or S3-compatible

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

## 🔐 Security

- ✅ JWT-based authentication
- ✅ Workflow ownership and access control
- ✅ Rate limiting (10-100 req/min per endpoint)
- ✅ File upload validation (type, size)
- ✅ CORS configuration
- ✅ Security headers
- ✅ Input sanitization
- ✅ Error monitoring

**Security Score**: 8/8 (100%) - Production ready

See [DEPLOYMENT_READINESS_AUDIT.md](DEPLOYMENT_READINESS_AUDIT.md) for full audit.

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **React Flow** - For the amazing canvas library
- **FastAPI** - For the excellent Python web framework
- **LangChain** - For AI orchestration tools
- **CrewAI** - For multi-agent systems
- **Supabase** - For auth and database
- **Vercel** - For frontend hosting

---

## 📧 Contact

- **GitHub**: [@Mettice](https://github.com/Mettice)
- **Issues**: [GitHub Issues](https://github.com/Mettice/Node-AI/issues)

---

## 🗺️ Roadmap

### **Current Version (v0.1.0 - Beta)**
- ✅ Visual workflow builder
- ✅ 30+ node types
- ✅ Real-time execution
- ✅ User authentication
- ✅ Workflow access control
- ✅ Rate limiting

### **Next (v0.2.0)**
- [ ] Workflow sharing and collaboration
- [ ] Team workspaces
- [ ] Advanced RBAC
- [ ] Workflow versioning
- [ ] API endpoints for workflows
- [ ] Webhook triggers

### **Future (v1.0.0)**
- [ ] Marketplace for workflows
- [ ] Custom node plugins
- [ ] Advanced analytics
- [ ] Billing and subscriptions
- [ ] Mobile app
- [ ] Self-hosted option

---

**Built with ❤️ by the NodeAI Team**

**⭐ Star this repo if you find it useful!**
