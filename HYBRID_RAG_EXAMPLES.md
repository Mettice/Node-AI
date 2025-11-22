# Hybrid RAG - Example Workflows

This document provides example workflows demonstrating how to use the Hybrid RAG system in NodeAI.

## Overview

Hybrid RAG combines:
- **Vector Search** (semantic similarity) - finds documents/content similar to the query
- **Knowledge Graph** (structured relationships) - finds entities and relationships
- **LLM Orchestration** (intelligent routing) - decides when to use which method

---

## Example 1: Biomedical Research Assistant

**Use Case**: Answer questions about research papers, authors, and citations.

### Workflow Structure

```
Text Input (Query)
    ├─→ Embed → Vector Search (Paper Content)
    │
    └─→ Knowledge Graph (Query) → Hybrid Retrieval → Chat
```

### Step-by-Step

1. **Create Knowledge Graph** (one-time setup)
   - Node: Knowledge Graph
   - Operation: `create_node`
   - Create nodes for:
     - Papers (labels: `Paper`, properties: `{title, abstract, year}`)
     - Authors (labels: `Author`, properties: `{name, affiliation}`)
     - Relationships:
       - `(Author)-[:WROTE]->(Paper)`
       - `(Paper)-[:CITES]->(Paper)`

2. **Vector Search Setup**
   - Node: Embed (OpenAI)
   - Node: Vector Store (FAISS)
   - Node: Vector Search

3. **Hybrid Retrieval**
   - Node: Hybrid Retrieval
   - Fusion Method: `reciprocal_rank`
   - Connect Vector Search and Knowledge Graph outputs

4. **Chat/Agent**
   - Node: Chat or LangChain Agent
   - Uses Hybrid Retrieval results to answer questions

### Example Queries

- **Semantic Query**: "What are the latest findings on CRISPR gene editing?"
  - Vector search finds semantically similar papers
  - Graph query finds related papers by citation network

- **Relationship Query**: "Find all papers by Dr. Smith and their collaborators"
  - Vector search: limited (needs exact name match)
  - Graph query: perfect (traverses author relationships)

- **Hybrid Query**: "What papers cite the most influential research on machine learning?"
  - Vector search: finds ML papers
  - Graph query: finds citation relationships
  - Hybrid: combines both for comprehensive results

---

## Example 2: Enterprise Knowledge Base

**Use Case**: Internal company knowledge with organizational relationships.

### Workflow Structure

```
Text Input (Query)
    ├─→ Embed → Vector Search (Documents)
    │
    └─→ Knowledge Graph (Query) → Hybrid Retrieval → Chat
```

### Knowledge Graph Schema

- **Nodes**:
  - `Document` (properties: `title, content, department`)
  - `Employee` (properties: `name, role, department`)
  - `Project` (properties: `name, status, description`)

- **Relationships**:
  - `(Employee)-[:AUTHORED]->(Document)`
  - `(Employee)-[:WORKS_ON]->(Project)`
  - `(Document)-[:RELATES_TO]->(Project)`

### Example Queries

- "Find documents about the Q4 project"
  - Vector: semantic similarity
  - Graph: project relationships

- "Who worked on the security audit?"
  - Vector: limited
  - Graph: employee-project relationships

---

## Example 3: Legal Document Analysis

**Use Case**: Case law research with citation networks.

### Knowledge Graph Schema

- **Nodes**:
  - `Case` (properties: `title, court, year, summary`)
  - `Judge` (properties: `name, court`)
  - `Statute` (properties: `title, code`)

- **Relationships**:
  - `(Case)-[:CITES]->(Case)`
  - `(Case)-[:CITES]->(Statute)`
  - `(Judge)-[:PRESIDED]->(Case)`

### Example Queries

- "Find cases similar to Brown v. Board of Education"
  - Vector: semantic similarity
  - Graph: citation network

- "What cases cite the Civil Rights Act?"
  - Vector: limited
  - Graph: citation relationships

---

## Example 4: Using LLM Agents with Graph Tools

**Use Case**: Intelligent query routing - let the LLM decide when to use vector vs graph.

### Workflow Structure

```
Text Input (Query)
    ├─→ Embed → Vector Search
    │
    ├─→ Knowledge Graph (Query)
    │
    └─→ LangChain Agent (with graph tools) → Hybrid Retrieval → Chat
```

### How It Works

1. **LangChain Agent** receives the user query
2. Agent analyzes the query and decides:
   - "Find papers by author X" → Use `find_related_entities` graph tool
   - "What is machine learning?" → Use vector search
   - "How are authors A and B connected?" → Use `find_paths` graph tool
3. Agent calls appropriate tools
4. Results are fused in Hybrid Retrieval
5. Final answer is generated

### Agent Configuration

- **Tools Available**:
  - Vector search (via connected node)
  - Graph tools (auto-added when Knowledge Graph node is connected):
    - `find_related_entities`
    - `find_paths`
    - `find_communities`
    - `find_influencers`
    - `find_similar_entities`

---

## Best Practices

### 1. When to Use Vector Search

- **Semantic queries**: "What is X?", "Explain Y"
- **Content similarity**: Finding similar documents
- **Fuzzy matching**: When exact relationships aren't known

### 2. When to Use Graph Queries

- **Relationship queries**: "Who worked with X?", "What cites Y?"
- **Path finding**: "How is A connected to B?"
- **Network analysis**: "Find communities", "Find influencers"

### 3. When to Use Hybrid Retrieval

- **Complex queries**: Need both semantic and relationship information
- **Comprehensive results**: Want to cover all angles
- **Unknown query type**: Let the system decide

### 4. Fusion Method Selection

- **Reciprocal Rank Fusion (RRF)**: Default, works well for most cases
- **Weighted**: When you know one source is more reliable
- **Simple Merge**: Quick deduplication, less sophisticated

---

## Configuration Tips

### Neo4j Setup

1. **Install Neo4j**:
   ```bash
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

2. **Set Environment Variables**:
   ```bash
   export NEO4J_URI=bolt://localhost:7687
   export NEO4J_USER=neo4j
   export NEO4J_PASSWORD=password
   ```

3. **Or Configure in Node**:
   - Set `neo4j_uri`, `neo4j_user`, `neo4j_password` in Knowledge Graph node config

### Performance Optimization

1. **Index Creation**: Create indexes on frequently queried properties
   ```cypher
   CREATE INDEX ON :Paper(title);
   CREATE INDEX ON :Author(name);
   ```

2. **Batch Operations**: Use `import` operation for bulk data loading

3. **Query Optimization**: Use specific relationship types and limits

---

## Troubleshooting

### Graph Tools Not Available in Agent

- **Check**: Neo4j connection is configured
- **Check**: Knowledge Graph node is connected upstream
- **Check**: Environment variables are set correctly

### No Results from Hybrid Retrieval

- **Check**: Both Vector Search and Knowledge Graph nodes are connected
- **Check**: Results are in the correct format
- **Check**: Fusion method is appropriate

### Slow Graph Queries

- **Add indexes** on frequently queried properties
- **Limit path depth** in path-finding queries
- **Use specific relationship types** instead of wildcards

---

## Next Steps

1. **Start Simple**: Create a small knowledge graph with a few nodes
2. **Test Queries**: Try both vector and graph queries separately
3. **Combine**: Use Hybrid Retrieval to fuse results
4. **Add Agents**: Let LLM agents intelligently route queries
5. **Scale**: Add more data and optimize queries

---

## Resources

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Hybrid RAG Analysis](./HYBRID_RAG_ANALYSIS.md)
- [Implementation Plan](./HYBRID_RAG_IMPLEMENTATION_PLAN.md)


All tasks completed
Neo4j Knowledge Graph node
Operations: create_node, create_relationship, query, import, export
Cypher query support
Graph data import/export
Hybrid Retrieval node
Combines vector search + graph queries
Fusion methods: RRF, Weighted, Simple Merge
Configurable weights
Detects results from upstream nodes
Graph Query Tools
5 pre-built tools: find_related_entities, find_paths, find_communities, find_influencers, find_similar_entities
LangChain tool definitions
LLM tool-calling integration
Graph tools auto-added to LangChain agents
Graph tools auto-added to CrewAI agents
Intelligent query routing (LLM decides when to use graph vs vector)
Frontend UI components
Knowledge Graph and Hybrid Retrieval nodes in palette
Custom forms with operation/fusion selectors
Node config display
Icons and styling
Documentation
Example workflows (biomedical, enterprise, legal)
Best practices guide
Troubleshooting tips
Configuration examples
How it works
User creates a workflow with:
Vector Search node (semantic similarity)
Knowledge Graph node (relationship queries)
Hybrid Retrieval node (combines both)
Optional: LangChain/CrewAI agent (intelligent routing)
Agents automatically get graph tools when Knowledge Graph is connected
LLM analyzes queries and calls appropriate tools:
"Find papers by author X" → find_related_entities
"What is machine learning?" → Vector search
"How are A and B connected?" → find_paths
Hybrid Retrieval fuses results using chosen method
Ready to use
The Hybrid RAG system is integrated and ready. You can:
Create knowledge graphs with Neo4j
Combine vector + graph search
Use LLM agents for intelligent query routing
Build workflows for research, enterprise knowledge, legal analysis, etc.
All nodes appear in your node palette. Start building.
