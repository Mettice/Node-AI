# Gemini File Search Integration Plan

## Overview

Google's new **File Search** feature simplifies RAG by handling the entire pipeline:
- Automatic file upload, chunking, embedding, and indexing
- No need for separate data loaders, text splitters, embedding models, or vector DBs
- Built-in semantic search with citations
- Supports 100+ file types
- $0.15 per million tokens to index (one-time), no storage fees

## Current Architecture vs. Gemini File Search

### Current Nodeflow RAG Pipeline:
```
File Loader → Chunk → Embed → Vector Store → Vector Search → Chat
```

### Gemini File Search Pipeline:
```
File Upload → File Search Store (auto-chunk, embed, index) → Chat with File Search tool
```

## Integration Strategy

### Option 1: New Dedicated Nodes
Create new nodes specifically for Gemini File Search, keeping it separate from the existing RAG pipeline.

**Nodes to Create:**
1. **Gemini File Search Store** - Create/manage File Search stores
2. **Gemini File Search Upload** - Upload files to a store
3. **Enhanced Chat Node** - Add File Search tool support to existing Gemini chat

### Option 2: Extend Existing Nodes (✅ IMPLEMENTED)
Add Gemini File Search as a provider option to existing nodes:
- Add to Vector Store node as a new provider
- Add to Chat node as a tool option

### Option 3: Hybrid Approach
Create new nodes but allow integration with existing workflow:
- File Search Store can be used as a Knowledge Base alternative
- Chat node can use File Search when Gemini provider is selected

## Implementation: Option 2 (Extend Existing Nodes) ✅

### 1. Vector Store Node (Extended)

**New Provider:** `gemini_file_search`

**Configuration:**
- `provider`: Select "gemini_file_search"
- `gemini_store_name` (string, optional): Existing store name (e.g., `fileSearchStores/my-store-123`). Leave empty to create new.
- `gemini_store_display_name` (string): Display name for new store (default: "Nodeflow File Search Store")
- `gemini_file_display_name` (string, optional): Display name for the file (defaults to filename)
- `gemini_max_tokens_per_chunk` (integer): Max tokens per chunk (default: 200)
- `gemini_max_overlap_tokens` (integer): Max overlap tokens (default: 20)
- `gemini_custom_metadata` (object, optional): Key-value pairs for filtering (e.g., `{"author": "John Doe", "year": 2024}`)

**Inputs:**
- `file_id` or `file_path` from File Loader node (no embeddings needed!)

**Outputs:**
- `index_id` (string): Store name (for compatibility with other providers)
- `store_name` (string): The File Search store name
- `file_name` (string): File name in the store
- `vectors_stored` (integer): Always 1 (File Search handles internally)

**Features:**
- Automatically creates store if not provided
- Uploads file and waits for processing (chunking, embedding, indexing)
- Supports custom chunking configuration
- Supports custom metadata for filtering

### 2. Chat Node (Enhanced - Gemini Provider)

**New Configuration Options:**
- `gemini_use_file_search` (boolean): Enable File Search tool (default: false)
- `gemini_file_search_stores` (array): List of store names to search (e.g., `["fileSearchStores/my-store-123"]`)
- `gemini_metadata_filter` (string, optional): Filter documents by metadata (e.g., `author=Robert Graves`)

**Outputs (Enhanced):**
- `response` (string): Chat response
- `citations` (array, optional): Citation information from `grounding_metadata`
- `file_search_used` (boolean): Whether File Search was used

## Implementation Details

### Backend Changes

#### 1. Add Dependencies
```python
# requirements.txt
google-genai>=0.2.0  # Ensure latest version with File Search support
```

#### 2. Create New Node Files

**`backend/nodes/storage/gemini_file_search_store.py`**
- Create, list, get, delete File Search stores
- Store management operations

**`backend/nodes/storage/gemini_file_search_upload.py`**
- Upload files to File Search stores
- Handle chunking configuration
- Track operation status

**`backend/nodes/llm/chat.py` (Enhancement)**
- Add File Search tool to Gemini chat
- Extract citations from responses
- Handle metadata filtering

#### 3. API Integration

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)

# Create store
file_search_store = client.file_search_stores.create(
    config={'display_name': 'my-store'}
)

# Upload file
operation = client.file_search_stores.upload_to_file_search_store(
    file='path/to/file.pdf',
    file_search_store_name=file_search_store.name,
    config={
        'display_name': 'My Document',
        'chunking_config': {
            'white_space_config': {
                'max_tokens_per_chunk': 200,
                'max_overlap_tokens': 20
            }
        }
    }
)

# Use in chat
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Your question here",
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[file_search_store.name],
                    metadata_filter="author=Robert Graves"  # Optional
                )
            )
        ]
    )
)
```

### Frontend Changes

#### 1. Node Definitions

Add new node types to the node registry:
- `gemini_file_search_store`
- `gemini_file_search_upload`

#### 2. Node Icons and Styling

- Use Google/Gemini branding colors
- Distinct icons for File Search nodes

#### 3. Configuration Forms

**File Search Store Node:**
- Simple form with display name input
- Store name (auto-generated, optional override)

**File Search Upload Node:**
- File selector (from File Loader)
- Store selector (from File Search Store nodes)
- Chunking configuration (optional)
- Metadata editor (key-value pairs)

**Chat Node (Enhanced):**
- Toggle for "Use File Search"
- Multi-select for File Search stores
- Metadata filter input

#### 4. Knowledge Base Integration

**Option A:** Add File Search stores to Knowledge Base Manager
- Show File Search stores alongside regular KBs
- Allow creating File Search stores from KB manager

**Option B:** Keep separate but allow cross-referencing
- File Search stores shown in a separate section
- Can be referenced in workflows

## Workflow Examples

### Example 1: Simple File Search RAG

```
1. File Loader → Upload document
2. Gemini File Search Store → Create store
3. Gemini File Search Upload → Upload file to store
4. Chat (Gemini) → Query with File Search enabled
```

### Example 2: Multiple Documents

```
1. File Loader → Upload multiple documents
2. Gemini File Search Store → Create store
3. Gemini File Search Upload (multiple) → Upload each file
4. Chat (Gemini) → Query across all documents
```

### Example 3: Filtered Search

```
1. File Loader → Upload documents with metadata
2. Gemini File Search Store → Create store
3. Gemini File Search Upload → Upload with custom metadata
4. Chat (Gemini) → Query with metadata filter
```

## Benefits of Integration

1. **Simplified RAG Setup**: No need for chunk, embed, and vector store nodes
2. **Better Accuracy**: Google's optimized embedding and retrieval
3. **Built-in Citations**: Automatic source attribution
4. **Cost Effective**: $0.15/M tokens indexing, no storage fees
5. **100+ File Types**: Broader support than current implementation
6. **Metadata Filtering**: Advanced query capabilities

## Migration Path

### For Existing Workflows:
- Keep existing RAG pipeline (File Loader → Chunk → Embed → Vector Store)
- Add File Search as an alternative option
- Users can choose based on their needs

### For New Workflows:
- Recommend File Search for simpler setups
- Use traditional pipeline for more control

## Pricing Considerations

**Indexing Cost:**
- $0.15 per million tokens to index files (one-time)
- No storage fees
- Only pay for model usage when context is used

**Comparison:**
- Current: Free (self-hosted FAISS) but requires infrastructure
- File Search: Pay-per-use, managed service

## Implementation Status

1. ✅ Analyze Gemini File Search API
2. ✅ Add `google-genai` dependency to requirements.txt
3. ✅ Extend Vector Store node with `gemini_file_search` provider
4. ✅ Enhance Chat node with File Search tool support
5. ✅ Add configuration options to node schemas
6. ⏳ Frontend automatically picks up schema changes (dynamic forms)
7. ⏳ Test File Search integration end-to-end
8. ⏳ Add to Knowledge Base Manager (optional future enhancement)
9. ⏳ Write tests
10. ✅ Update documentation

## API Reference

- [Gemini File Search Documentation](https://ai.google.dev/gemini-api/docs/file-search)
- [File Search Store API](https://ai.google.dev/api/rest/v1beta/fileSearchStores)
- [File Search Tool](https://ai.google.dev/api/rest/v1beta/Tool#FileSearch)

## Notes

- File Search stores are globally scoped (names must be unique)
- Files uploaded via File API are deleted after 48 hours
- Data imported into File Search stores persists indefinitely
- Supports models: `gemini-2.5-pro`, `gemini-2.5-flash`
- Chunking uses `gemini-embedding-001` model internally

