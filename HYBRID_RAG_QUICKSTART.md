# Hybrid RAG Quick Start Guide 🚀

## 1. Start Neo4j

**Using Docker (Easiest):**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**Verify it's running:**
- Open http://localhost:7474 in your browser
- Login with: `neo4j` / `password`

## 2. Start the Backend

```bash
cd backend
python main.py
```

## 3. Start the Frontend

```bash
cd frontend
npm run dev
```

## 4. Test the Hybrid RAG System

### Option A: Load Demo Workflow (Recommended)

1. Open the app at http://localhost:5173
2. Click **"Load Workflow"** in the sidebar
3. Select **`hybrid_rag_demo.json`**
4. You'll see a complete workflow with:
   - 📝 Text Input (your query)
   - 🕸️ Knowledge Graph (import sample data)
   - 🔍 Graph Query (find related papers)
   - 🔎 Vector Search (semantic similarity)
   - 🔀 Hybrid Retrieval (fusion)
   - 💬 Chat (generate answer)

5. Click **"Run Workflow"** and watch:
   - Smooth curved edges animate with flowing particles
   - Nodes turn blue as they process
   - Results appear in the right panel

### Option B: Build Your Own

1. **Add Nodes** from the palette:
   - Drag `Text Input` → enter your query
   - Drag `Knowledge Graph` → configure Neo4j connection
   - Drag `Hybrid Retrieval` → configure fusion method
   - Drag `Chat` → configure LLM

2. **Connect them** by dragging from handles

3. **Configure each node** in the Properties panel

4. **Run!** Click the play button

## 5. What to Expect

### Visual Features ✨
- **Curved Bezier edges** connecting nodes smoothly
- **Animated particles** flowing through edges during execution
- **Color-coded status**: 
  - Gray = idle
  - Blue = running
  - Green = completed
  - Red = error

### Hybrid RAG Features 🎯
- **Vector Search**: Finds semantically similar content
- **Knowledge Graph**: Finds structurally related content
- **Fusion Methods**:
  - `reciprocal_rank`: Best for balanced results
  - `weighted`: Custom control (70% vector, 30% graph)
  - `simple_merge`: Fastest, no ranking

### Error Handling 🛡️
If something goes wrong, you'll get clear messages like:
- ❌ "Cannot connect to Neo4j at bolt://localhost:7687"
  → Check if Neo4j is running
- ❌ "Neo4j authentication failed"
  → Check username/password
- ❌ "No results found from either source"
  → Ensure nodes are connected properly

## 6. Try Different Configurations

### Change Fusion Method
1. Select the `Hybrid Retrieval` node
2. In Properties panel, change **Fusion Method**
3. For `weighted`, adjust the sliders:
   - More vector weight = favor semantic similarity
   - More graph weight = favor relationships

### Test with LLM Agents
1. Replace `Chat` node with `LangChain Agent` or `CrewAI Agent`
2. The agent can now use 5 graph query tools:
   - `find_related_entities`
   - `find_paths`
   - `find_communities`
   - `find_influencers`
   - `find_similar_entities`
3. The agent will intelligently choose which tool to use!

## 7. Troubleshooting

**Neo4j won't start?**
```bash
# Check if port is already in use
docker ps
docker stop neo4j && docker rm neo4j
# Then run the docker command again
```

**Nodes not appearing in UI?**
- Restart the backend: `Ctrl+C` then `python main.py`
- Clear browser cache and refresh

**Import failing?**
- Verify Neo4j connection in the node config
- Check the console for detailed error messages

## Next Steps

- Read `HYBRID_RAG_EXAMPLES.md` for more advanced workflows
- Try with your own data
- Experiment with different fusion methods
- Add more nodes like `Rerank` for better results

**Enjoy exploring Hybrid RAG!** 🎉

