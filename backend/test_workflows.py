"""
Test script for NodeAI workflow execution.

This script tests various workflows from simple to complex RAG pipelines.
Run it with: python test_workflows.py
"""

import asyncio
import json
from datetime import datetime

import httpx

# API base URL
API_BASE = "http://localhost:8000/api/v1"


async def test_health_check():
    """Test health check endpoint."""
    print("\n" + "=" * 60)
    print("1. Testing Health Check")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_list_nodes():
    """Test listing all nodes."""
    print("\n" + "=" * 60)
    print("2. Testing List Nodes")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/nodes")
        nodes = response.json()
        print(f"Found {len(nodes)} nodes:")
        for node in nodes:
            print(f"  - {node['type']}: {node['name']} ({node['category']})")


async def test_simple_text_input():
    """Test simple text input workflow."""
    print("\n" + "=" * 60)
    print("3. Testing Simple Text Input Workflow")
    print("=" * 60)
    
    workflow = {
        "name": "Simple Text Input",
        "nodes": [
            {
                "id": "1",
                "type": "text_input",
                "position": {"x": 0, "y": 0},
                "data": {
                    "text": "Hello world! This is a simple test of the text input node."
                },
            }
        ],
        "edges": [],
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE}/workflows/execute",
            json={"workflow": workflow},
        )
        
        if response.status_code == 200:
            result = response.json()
            execution_id = result["execution_id"]
            print(f"✅ Execution started: {execution_id}")
            print(f"Status: {result['status']}")
            
            # Get execution details
            exec_response = await client.get(f"{API_BASE}/executions/{execution_id}")
            execution = exec_response.json()
            
            print(f"\nExecution Results:")
            print(f"  Status: {execution['status']}")
            print(f"  Total Cost: ${execution['total_cost']:.4f}")
            print(f"  Duration: {execution.get('duration_ms', 0)}ms")
            
            if execution["results"]:
                node_id = list(execution["results"].keys())[0]
                node_result = execution["results"][node_id]
                print(f"\nNode {node_id} Output:")
                if node_result.get("output"):
                    print(f"  {json.dumps(node_result['output'], indent=2)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)


async def test_chunk_workflow():
    """Test text input + chunk workflow."""
    print("\n" + "=" * 60)
    print("4. Testing Text Input + Chunk Workflow")
    print("=" * 60)
    
    workflow = {
        "name": "Text Chunking",
        "nodes": [
            {
                "id": "1",
                "type": "text_input",
                "position": {"x": 0, "y": 0},
                "data": {
                    "text": (
                        "This is a longer text document that we want to split into chunks. "
                        "It contains multiple sentences and paragraphs. "
                        "The chunking node will split this text into smaller pieces. "
                        "Each chunk will have a specific size and overlap with adjacent chunks. "
                        "This is useful for processing large documents in smaller pieces."
                    ),
                },
            },
            {
                "id": "2",
                "type": "chunk",
                "position": {"x": 200, "y": 0},
                "data": {
                    "strategy": "recursive",
                    "chunk_size": 100,
                    "chunk_overlap": 20,
                },
            },
        ],
        "edges": [
            {"id": "e1", "source": "1", "target": "2"},
        ],
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE}/workflows/execute",
            json={"workflow": workflow},
        )
        
        if response.status_code == 200:
            result = response.json()
            execution_id = result["execution_id"]
            print(f"✅ Execution started: {execution_id}")
            
            # Get execution details
            exec_response = await client.get(f"{API_BASE}/executions/{execution_id}")
            execution = exec_response.json()
            
            print(f"\nExecution Results:")
            print(f"  Status: {execution['status']}")
            print(f"  Total Cost: ${execution['total_cost']:.4f}")
            
            if execution["results"].get("2"):
                chunk_result = execution["results"]["2"]
                if chunk_result.get("output"):
                    output = chunk_result["output"]
                    print(f"\nChunking Results:")
                    print(f"  Strategy: {output.get('strategy')}")
                    print(f"  Chunks created: {output.get('count')}")
                    print(f"  Avg chunk size: {output.get('avg_chunk_size')} chars")
                    if output.get("chunks"):
                        print(f"\nFirst 3 chunks:")
                        for i, chunk in enumerate(output["chunks"][:3], 1):
                            print(f"  Chunk {i}: {chunk[:50]}...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)


async def test_embed_workflow():
    """Test text input + embed workflow."""
    print("\n" + "=" * 60)
    print("5. Testing Text Input + Embed Workflow")
    print("=" * 60)
    
    workflow = {
        "name": "Text Embedding",
        "nodes": [
            {
                "id": "1",
                "type": "text_input",
                "position": {"x": 0, "y": 0},
                "data": {
                    "text": "This is a test document for embedding.",
                },
            },
            {
                "id": "2",
                "type": "embed",
                "position": {"x": 200, "y": 0},
                "data": {
                    "provider": "openai",
                    "openai_model": "text-embedding-3-small",
                },
            },
        ],
        "edges": [
            {"id": "e1", "source": "1", "target": "2"},
        ],
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE}/workflows/execute",
            json={"workflow": workflow},
        )
        
        if response.status_code == 200:
            result = response.json()
            execution_id = result["execution_id"]
            print(f"✅ Execution started: {execution_id}")
            
            # Get execution details
            exec_response = await client.get(f"{API_BASE}/executions/{execution_id}")
            execution = exec_response.json()
            
            print(f"\nExecution Results:")
            print(f"  Status: {execution['status']}")
            print(f"  Total Cost: ${execution['total_cost']:.4f}")
            
            if execution["results"].get("2"):
                embed_result = execution["results"]["2"]
                if embed_result.get("output"):
                    output = embed_result["output"]
                    print(f"\nEmbedding Results:")
                    print(f"  Provider: {output.get('provider')}")
                    print(f"  Model: {output.get('model')}")
                    print(f"  Embeddings created: {output.get('count')}")
                    print(f"  Dimension: {output.get('dimension')}")
                    if output.get("embeddings"):
                        print(f"  First embedding (first 5 values): {output['embeddings'][0][:5]}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)


async def test_full_rag_workflow():
    """Test complete RAG pipeline."""
    print("\n" + "=" * 60)
    print("6. Testing Full RAG Pipeline")
    print("=" * 60)
    print("This will test: Text Input → Chunk → Embed → Store → Search → Chat")
    print("Note: This requires OpenAI API key and may take a minute...")
    
    workflow = {
        "name": "Full RAG Pipeline",
        "nodes": [
            {
                "id": "1",
                "type": "text_input",
                "position": {"x": 0, "y": 0},
                "data": {
                    "text": (
                        "NodeAI is a visual workflow builder for RAG pipelines. "
                        "Users can drag and drop nodes to build AI workflows. "
                        "It supports multiple embedding providers like OpenAI and HuggingFace. "
                        "Vector storage options include FAISS and Pinecone. "
                        "The system tracks costs and provides execution traces."
                    ),
                },
            },
            {
                "id": "2",
                "type": "chunk",
                "position": {"x": 200, "y": 0},
                "data": {
                    "strategy": "recursive",
                    "chunk_size": 100,
                    "chunk_overlap": 20,
                },
            },
            {
                "id": "3",
                "type": "embed",
                "position": {"x": 400, "y": 0},
                "data": {
                    "provider": "openai",
                    "openai_model": "text-embedding-3-small",
                },
            },
            {
                "id": "4",
                "type": "vector_store",
                "position": {"x": 600, "y": 0},
                "data": {
                    "provider": "faiss",
                    "faiss_index_type": "flat",
                },
            },
            {
                "id": "5",
                "type": "text_input",
                "position": {"x": 400, "y": 200},
                "data": {
                    "text": "What is NodeAI?",
                },
            },
            {
                "id": "6",
                "type": "embed",
                "position": {"x": 600, "y": 200},
                "data": {
                    "provider": "openai",
                    "openai_model": "text-embedding-3-small",
                },
            },
            {
                "id": "7",
                "type": "vector_search",
                "position": {"x": 800, "y": 200},
                "data": {
                    "provider": "faiss",
                    "query": "What is NodeAI?",
                    "top_k": 3,
                    "index_id": "",  # Will be set from node 4 output
                },
            },
            {
                "id": "8",
                "type": "chat",
                "position": {"x": 1000, "y": 200},
                "data": {
                    "provider": "openai",
                    "openai_model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 200,
                    "system_prompt": "You are a helpful assistant.",
                    "user_prompt_template": "Context: {context}\n\nQuestion: {query}\n\nAnswer:",
                },
            },
        ],
        "edges": [
            {"id": "e1", "source": "1", "target": "2"},
            {"id": "e2", "source": "2", "target": "3"},
            {"id": "e3", "source": "3", "target": "4"},
            {"id": "e4", "source": "5", "target": "6"},  # Query text → Embed
            {"id": "e5", "source": "4", "target": "7"},  # index_id to search
            {"id": "e6", "source": "6", "target": "7"},  # query_embedding to search
            {"id": "e7", "source": "7", "target": "8"},  # Search results → Chat
        ],
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("\n⏳ Executing workflow (this may take a minute)...")
        response = await client.post(
            f"{API_BASE}/workflows/execute",
            json={"workflow": workflow},
        )
        
        if response.status_code == 200:
            result = response.json()
            execution_id = result["execution_id"]
            print(f"✅ Execution started: {execution_id}")
            
            # Get execution details
            exec_response = await client.get(f"{API_BASE}/executions/{execution_id}")
            execution = exec_response.json()
            
            print(f"\nExecution Results:")
            print(f"  Status: {execution['status']}")
            print(f"  Total Cost: ${execution['total_cost']:.4f}")
            # Calculate duration from timestamps if available
            if execution.get('started_at') and execution.get('completed_at'):
                from datetime import datetime
                started_str = execution['started_at']
                completed_str = execution['completed_at']
                # Handle both ISO format with and without Z
                started = datetime.fromisoformat(started_str.replace('Z', '+00:00'))
                completed = datetime.fromisoformat(completed_str.replace('Z', '+00:00'))
                duration_ms = int((completed - started).total_seconds() * 1000)
                print(f"  Duration: {duration_ms}ms ({duration_ms/1000:.2f}s)")
            else:
                print(f"  Duration: {execution.get('duration_ms', 0)}ms")
            
            # Show results from each node
            print(f"\nNode Results:")
            for node_id in sorted(execution["results"].keys(), key=lambda x: int(x) if x.isdigit() else 999):
                node_result = execution["results"][node_id]
                status = node_result.get('status', 'unknown')
                status_icon = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
                print(f"  {status_icon} Node {node_id} ({status}):")
                
                if node_result.get("error"):
                    print(f"    Error: {node_result['error']}")
                
                if node_result.get("output"):
                    output = node_result["output"]
                    if node_id == "8":  # Chat node
                        response = output.get('response', '')
                        if response:
                            print(f"    Response: {response[:200]}...")
                        else:
                            print(f"    Response: (empty)")
                            print(f"    Output keys: {list(output.keys())}")
                    elif node_id == "7":  # Search node
                        print(f"    Results found: {output.get('results_count', 0)}")
                        results = output.get("results")
                        if results and len(results) > 0:
                            top_result = results[0]
                            if isinstance(top_result, dict):
                                result_text = top_result.get('text')
                                if result_text:
                                    print(f"    Top result: {str(result_text)[:80]}...")
                                    print(f"    Score: {top_result.get('score', 0):.4f}")
                                else:
                                    # Try to get from metadata
                                    meta = top_result.get('metadata', {})
                                    meta_text = meta.get('text') if isinstance(meta, dict) else None
                                    if meta_text:
                                        print(f"    Top result (from metadata): {str(meta_text)[:80]}...")
                                    else:
                                        print(f"    Top result: (text not found)")
                                        print(f"    Result structure: {json.dumps(top_result, indent=4, default=str)[:200]}...")
                            else:
                                print(f"    Top result: {str(top_result)[:50]}...")
                    elif node_id == "4":  # Store node
                        print(f"    Index ID: {output.get('index_id', '')}")
                        print(f"    Vectors stored: {output.get('vectors_stored', 0)}")
                    elif node_id == "6":  # Query embed node
                        print(f"    Embeddings created: {output.get('count', 0)}")
                        print(f"    Dimension: {output.get('dimension', 0)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NodeAI Workflow Test Suite")
    print("=" * 60)
    print(f"Testing API at: {API_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Basic tests
        await test_health_check()
        await test_list_nodes()
        
        # Simple workflow tests
        await test_simple_text_input()
        await test_chunk_workflow()
        await test_embed_workflow()
        
        # Full RAG pipeline (requires API keys)
        print("\n" + "=" * 60)
        print("Full RAG Pipeline Test")
        print("=" * 60)
        print("⚠️  This test requires OpenAI API key and will make API calls.")
        response = input("Run full RAG pipeline test? (y/n): ")
        if response.lower() == "y":
            await test_full_rag_workflow()
        else:
            print("Skipping full RAG pipeline test.")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to API.")
        print("Make sure the server is running: uvicorn backend.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

