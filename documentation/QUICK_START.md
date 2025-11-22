# NodAI Quick Start Guide

Get up and running in 5 minutes!

---

## ⚡ 5-Minute Setup

### 1. Install Dependencies (2 minutes)

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Configure API Keys (1 minute)

Create `.env` in project root:
```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Start Servers (1 minute)

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn backend.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Create Your First Workflow (1 minute)

1. Open `http://localhost:5173`
2. Click the **"+"** button on canvas
3. Add **"Text Input"** node
4. Add **"Chat"** node
5. Connect them
6. Configure Chat node:
   - Provider: OpenAI
   - Model: gpt-3.5-turbo
   - Prompt: `Answer: {{text_input.text}}`
7. Click **"Run"**!

---

## 🎯 Common Use Cases

### Document Q&A (3 minutes)

1. **Add File Loader** → Upload a PDF
2. **Add Chunk** → Connect to File Loader
3. **Add Embed** → Connect to Chunk
4. **Add Vector Store** → Connect to Embed
5. **Add Text Input** → Enter your question
6. **Add Vector Search** → Connect to Text Input and Vector Store
7. **Add Chat** → Connect to Vector Search
   - Prompt: `Context: {{vector_search.results}}\nQuestion: {{text_input.text}}\nAnswer:`

### Content Summarization (2 minutes)

1. **Add File Loader** → Upload document
2. **Add Chunk** → Split into sections
3. **Add Chat** → Connect to Chunk
   - Prompt: `Summarize: {{chunk.text}}`

### Multi-Agent Task (5 minutes)

1. **Add Text Input** → Describe task
2. **Add CrewAI Agent** → Configure agents and tools
3. **Add Chat** → Format final output

---

## 🚀 Deploy Your Workflow

1. **Save** your workflow
2. **Click "Deploy"** in top toolbar
3. **Get API endpoint:**
   ```
   POST /api/v1/workflows/{workflow_id}/query
   ```
4. **Query it:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/workflows/{id}/query \
     -H "Content-Type: application/json" \
     -d '{"input": {"query": "Your question"}}'
   ```

---

## 📚 Next Steps

- **Full Guide:** See [GETTING_STARTED.md](./GETTING_STARTED.md)
- **User Guide:** See [USER_GUIDE.md](./USER_GUIDE.md)
- **Examples:** Check `data/workflows/` folder
- **API Docs:** Visit `http://localhost:8000/docs`

---

**That's it! You're ready to build! 🎉**

