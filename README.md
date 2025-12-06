# 🎨 Nodeflow - Visual GenAI Workflow Builder

**Build, deploy, and manage production-ready AI applications visually. No code required.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-19.1-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)

---

## 📋 Summary

**Nodeflow** is a visual, no-code platform for building enterprise-grade AI applications. Think of it as "n8n for AI" or "LangGraph with a visual interface" - enabling teams to build sophisticated RAG systems, multi-agent workflows, and custom AI pipelines through an intuitive drag-and-drop canvas.

### What Makes Nodeflow Different?

- **🎯 Complete GenAI Stack**: End-to-end RAG pipeline (Vector + BM25 + Knowledge Graph) in one platform
- **🤖 Multi-Agent Orchestration**: Coordinate multiple AI agents (CrewAI, LangChain) for complex tasks
- **🧠 Intelligent Routing**: AI-powered semantic data mapping between nodes (no manual configuration)
- **💰 Cost Intelligence**: Real-time cost tracking, forecasting, and optimization recommendations
- **📊 Production-Ready**: Built-in evaluation, A/B testing, observability, and deployment
- **🔌 Unified AI Interface**: Support for OpenAI, Anthropic, Google Gemini, Groq, and more

**Perfect for**: AI consultants, product teams, data scientists, and enterprises building production AI applications.

---

## ✨ Key Features

### **🎯 Visual Workflow Builder**
- **Drag-and-drop canvas** for building AI workflows visually
- **Real-time execution** with streaming updates and visual feedback
- **31+ pre-built node types** covering the complete GenAI stack
- **Workflow templates** for common use cases (RAG, multi-agent, document processing)
- **Intelligent data routing** - AI automatically maps data between nodes
- **Visual debugging** - See data flow, node states, and execution traces

### **🤖 Complete RAG Pipeline**
- **Hybrid Retrieval**: Combines Vector Search + BM25 Keyword Search + Knowledge Graph queries
- **Multiple Vector Stores**: Pinecone, Chroma, FAISS, Neo4j
- **Embedding Providers**: OpenAI, Voyage AI, Cohere, local models
- **Reranking**: Cohere and Voyage AI reranking for improved relevance
- **Knowledge Bases**: Build, version, and query document repositories
- **Advanced Chunking**: Semantic chunking with configurable size and overlap
- **RAG Evaluation**: Test workflows with Q&A datasets, measure accuracy and relevance

### **🚀 Multi-Agent Systems**
- **CrewAI Integration**: Build complex multi-agent workflows with role-based agents
- **LangChain Agents**: Tool-using agents with access to external APIs
- **Agent Lightning**: Optional RL/APO optimization for automatic agent improvement
- **Task Orchestration**: Define agent roles, goals, and task dependencies
- **Collaborative Agents**: Agents can collaborate, share context, and build on each other's work

### **💬 LLM Integrations**
- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5, GPT-4o, GPT-4o-mini
- **Anthropic**: Claude 3 Opus, Sonnet, Haiku (all versions)
- **Google Gemini**: Gemini Pro, Gemini Ultra with File Search and URL Context
- **Groq**: Ultra-fast inference for real-time applications
- **Unified Interface**: Switch between providers without changing your workflow

### **📄 Document Processing**
- **Universal File Loader**: PDF, DOCX, TXT, Markdown, HTML
- **Image Processing**: OCR (Tesseract), Vision analysis (GPT-4 Vision, Gemini Vision)
- **Audio Processing**: Transcription (Whisper), audio analysis
- **Video Processing**: Frame extraction and analysis
- **Structured Data**: CSV, Excel, JSON, Parquet support
- **Batch Processing**: Process multiple files simultaneously

### **🔍 Advanced NLP**
- **Text Analysis**: Sentiment analysis, NER, keyword extraction, summarization
- **Translation**: Multi-language translation support
- **Readability Scoring**: Analyze text complexity and readability
- **Content Classification**: Categorize and classify text content
- **Custom NLP Tasks**: Extend with custom NLP pipelines

### **💰 Cost Intelligence**
- **Real-Time Tracking**: Track costs per node, workflow, and execution
- **Cost Analytics**: Daily, weekly, monthly cost breakdowns
- **Forecasting**: Predict future costs based on usage patterns
- **Optimization Recommendations**: AI-powered suggestions to reduce costs
- **ROI Analysis**: Calculate return on investment for AI workflows
- **Budget Alerts**: Set budgets and receive notifications

### **📊 Observability & Monitoring**
- **Execution Traces**: Detailed traces of every workflow execution
- **Performance Metrics**: Latency, throughput, error rates
- **Cost Per Query**: Track costs at granular levels
- **Quality Trends**: Monitor accuracy and relevance over time
- **Error Tracking**: Integrated Sentry error monitoring
- **Real-Time Dashboards**: Visual analytics and reporting

### **🧪 Testing & Evaluation**
- **RAG Evaluation**: Test workflows with Q&A datasets
- **A/B Testing**: Compare different workflow configurations
- **Quality Metrics**: Accuracy, relevance, latency, cost per query
- **Automated Testing**: Run evaluations on schedule
- **Quality Trends**: Track performance over time

### **🚢 Deployment & Integration**
- **One-Click Deployment**: Deploy workflows as API endpoints
- **Embeddable Widgets**: Embed workflows into websites
- **Webhook Triggers**: Trigger workflows via HTTP requests
- **API Access**: RESTful API for all operations
- **Version Control**: Workflow versioning and rollback
- **Health Monitoring**: Deployment health checks

### **🔐 Enterprise Security**
- **JWT Authentication**: Secure authentication via Supabase
- **Workflow Access Control**: Fine-grained permissions
- **Rate Limiting**: Configurable rate limits per endpoint
- **File Upload Validation**: Type and size validation
- **CORS Configuration**: Secure cross-origin requests
- **Security Headers**: Production-ready security headers
- **Input Sanitization**: Protection against injection attacks

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Node.js 18+
- Supabase account ([free tier available](https://supabase.com))

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
# Edit .env with your API keys and Supabase credentials

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
3. Verify email (check Supabase dashboard in dev mode)
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
│  - Cost analytics dashboards                │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│        FastAPI Backend                      │
│  - Workflow execution engine                │
│  - Node registry (31+ node types)           │
│  - Intelligent data routing                 │
│  - Streaming via Server-Sent Events         │
│  - Cost tracking & analytics                │
│  - RAG evaluation engine                    │
│  - JWT authentication                       │
└──────┬──────────────────────────────────────┘
       │
       ├─────────────────┬─────────────────┬──────────────┐
       ▼                 ▼                 ▼              ▼
  Supabase          AI APIs           Vector DBs      Knowledge Graph
  Auth/DB      (OpenAI, Claude,    (Pinecone,      (Neo4j)
               Gemini, Groq)        Chroma, FAISS)
```

---

## 🎯 Use Cases

### **1. RAG Applications** 📚
Build production-ready retrieval-augmented generation systems:
- **Customer Support Chatbots**: Answer questions from knowledge bases
- **Document Q&A Systems**: Query PDFs, documents, and manuals
- **Research Assistants**: Search and synthesize information
- **Internal Knowledge Bases**: Company wikis and documentation

**Features Used**: Vector Search, BM25, Knowledge Graph, Reranking, Evaluation

### **2. Multi-Agent Systems** 🤖
Create complex AI workflows with multiple specialized agents:
- **Content Creation**: Research → Writing → Editing → Publishing
- **Data Analysis**: Data collection → Analysis → Reporting → Visualization
- **Customer Onboarding**: Document verification → Risk assessment → Account setup
- **Research Workflows**: Literature review → Analysis → Report generation

**Features Used**: CrewAI, LangChain Agents, Agent Lightning, Task Orchestration

### **3. Document Processing** 📄
Process and analyze documents at scale:
- **Contract Analysis**: Extract clauses, terms, and key information
- **Invoice Processing**: Extract data, validate, and route
- **Medical Records**: Extract patient information, analyze notes
- **Legal Document Review**: Classify, extract, and summarize documents

**Features Used**: File Loader, OCR, Vision, Advanced NLP, Chunking

### **4. Custom AI Pipelines** 🔧
Build any AI application you can imagine:
- **Content Moderation**: Analyze and classify user-generated content
- **Sentiment Analysis**: Monitor brand sentiment across channels
- **Data Transformation**: Extract, transform, and load data with AI
- **API Orchestration**: Chain multiple APIs with AI decision-making

**Features Used**: All node types, Intelligent Routing, Custom Logic

---

## 🛠️ Technology Stack

### **Frontend**
- **React 19.1** - Modern UI framework
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool
- **React Flow** - Visual workflow canvas
- **Zustand** - State management
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Animations
- **Lucide Icons** - Icon library

### **Backend**
- **Python 3.11+** - Modern Python features
- **FastAPI** - High-performance web framework
- **Pydantic** - Data validation
- **LangChain** - AI orchestration
- **CrewAI** - Multi-agent systems
- **Supabase** - Auth and database
- **PostgreSQL** - Relational database
- **Sentry** - Error monitoring

### **AI Integrations**
- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5, GPT-4o, GPT-4o-mini
- **Anthropic**: Claude 3 Opus, Sonnet, Haiku (all versions)
- **Google Gemini**: Gemini Pro, Ultra (with File Search & URL Context)
- **Groq**: Ultra-fast inference
- **Cohere**: Reranking and embeddings
- **Voyage AI**: High-quality embeddings

### **Vector Stores & Databases**
- **Pinecone** - Managed vector database
- **Chroma** - Open-source vector store
- **FAISS** - Facebook AI Similarity Search
- **Neo4j** - Knowledge graph database
- **PostgreSQL** - Relational database (via Supabase)

### **Additional Tools**
- **Tesseract OCR** - Text extraction from images
- **Whisper** - Audio transcription
- **Rank-BM25** - Keyword-based retrieval
- **NLTK** - Natural language processing
- **LangSmith** - LangChain observability
- **Langfuse** - LLM observability

---

## 📦 Deployment

### **Recommended: Separate Deployments**

- **Frontend**: Vercel (React/Vite) → [Deploy Guide](SIMPLE_DEPLOYMENT.md)
- **Backend**: Railway (FastAPI) → [Deploy Guide](SIMPLE_DEPLOYMENT.md)
- **Database**: Supabase (PostgreSQL + Auth)
- **Monitoring**: Sentry

**Deploy Time**: ~10 minutes  
**Cost**: $0-5/month for beta testing

See [SIMPLE_DEPLOYMENT.md](SIMPLE_DEPLOYMENT.md) for complete step-by-step instructions.

---

## 🔐 Security

- ✅ **JWT-based authentication** via Supabase
- ✅ **Workflow ownership** and access control
- ✅ **Rate limiting** (10-100 req/min per endpoint)
- ✅ **File upload validation** (type, size)
- ✅ **CORS configuration** for secure cross-origin requests
- ✅ **Security headers** (X-Frame-Options, CSP, etc.)
- ✅ **Input sanitization** against injection attacks
- ✅ **Error monitoring** with Sentry

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
- **Railway** - For backend hosting

---

## 📧 Contact

- **GitHub**: [@Mettice](https://github.com/Mettice)
- **Issues**: [GitHub Issues](https://github.com/Mettice/Node-AI/issues)

---

## 🗺️ Roadmap

### **Current Version (v0.1.0 - Beta)**
- ✅ Visual workflow builder
- ✅ 31+ node types
- ✅ Real-time execution
- ✅ User authentication
- ✅ Workflow access control
- ✅ Rate limiting
- ✅ Cost tracking & analytics
- ✅ RAG evaluation
- ✅ Multi-agent orchestration
- ✅ Intelligent routing
- ✅ Hybrid RAG (Vector + BM25 + Graph)

### **Next (v0.2.0)**
- [ ] Workflow sharing and collaboration
- [ ] Team workspaces
- [ ] Advanced RBAC
- [ ] Workflow versioning
- [ ] API endpoints for workflows
- [ ] Email trigger nodes
- [ ] Scheduled workflows

### **Future (v1.0.0)**
- [ ] Marketplace for workflows
- [ ] Custom node plugins
- [ ] Advanced analytics
- [ ] Billing and subscriptions
- [ ] Mobile app
- [ ] Self-hosted option
- [ ] Workflow templates marketplace

---

**Built with ❤️ by the Nodeflow Team**

**⭐ Star this repo if you find it useful!**
