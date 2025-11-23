# Phase 3: Complete RAG Pipeline

**Duration:** Week 6-7  
**Status:** 🔄 Not Started  
**Prerequisites:** [Phase 2: Frontend Canvas](./PHASE_2_FRONTEND_CANVAS.md)

---

## 🎯 Goals

- Add remaining essential nodes
- Support file uploads
- Improve chunking strategies
- Add more storage options

---

## 📋 Tasks

### Backend: Additional Nodes

#### 1. Upload File Node (`backend/nodes/input/upload.py`)

- [ ] Accept file uploads:
  - PDF files
  - DOCX files
  - TXT files
  - MD files

- [ ] Extract text from files:
  - Use appropriate parser for each type
  - Handle encoding issues
  - Extract metadata (filename, size, type)

- [ ] Output format:
  ```python
  {
      "text": str,
      "metadata": {
          "filename": str,
          "file_type": str,
          "file_size": int,
          "pages": int  # for PDFs
      }
  }
  ```

- [ ] Configuration:
  - `auto_parse`: bool (default: True)
  - `extract_metadata`: bool (default: True)

- [ ] Error handling:
  - Invalid file type
  - Corrupted files
  - File size limits

- [ ] Unit tests

#### 2. PDF Parser Node (`backend/nodes/processing/pdf_parser.py`)

- [ ] Extract text from PDF:
  - Use PyPDF2 or pdfplumber
  - Handle multi-page documents
  - Preserve formatting (optional)

- [ ] Extract tables:
  - Use pdfplumber or camelot
  - Return tables as structured data
  - Option to convert to markdown

- [ ] OCR for images (optional):
  - Use Tesseract or cloud OCR
  - Extract text from images in PDF
  - Combine with text extraction

- [ ] Page range selection:
  - `page_range`: str (e.g., "1-5", "all")
  - Parse range string
  - Extract only specified pages

- [ ] Output format:
  ```python
  {
      "text": str,
      "tables": List[Dict],
      "images": List[Dict],  # if OCR enabled
      "metadata": {
          "pages_processed": int,
          "tables_found": int,
          "images_found": int
      }
  }
  ```

- [ ] Configuration:
  - `extract_tables`: bool (default: False)
  - `ocr_for_images`: bool (default: False)
  - `page_range`: str (default: "all")

- [ ] Unit tests

#### 3. Metadata Enricher Node (`backend/nodes/processing/metadata.py`)

- [ ] Auto-extract dates:
  - Use regex or date parser
  - Extract dates from text
  - Add to metadata

- [ ] Add source filename:
  - Extract from previous nodes
  - Add to chunk metadata

- [ ] Custom fields:
  - Key-value pairs
  - Add to all chunks
  - Support templating

- [ ] Output format:
  ```python
  {
      "chunks": List[Dict],
      "metadata": Dict  # enriched metadata
  }
  ```

- [ ] Configuration:
  - `auto_extract_dates`: bool (default: True)
  - `add_source_filename`: bool (default: True)
  - `custom_fields`: Dict[str, Any] (default: {})

- [ ] Unit tests

#### 4. Filter Node (`backend/nodes/processing/filter.py`)

- [ ] Filter chunks by condition:
  - Contains text
  - Regex match
  - Length check
  - Custom function

- [ ] Action options:
  - Keep matching chunks
  - Remove matching chunks

- [ ] Output format:
  ```python
  {
      "chunks": List[str],
      "filtered_count": int,
      "removed_count": int
  }
  ```

- [ ] Configuration:
  - `condition`: str (enum: "contains", "regex", "length")
  - `value`: str or int
  - `action`: str (enum: "keep", "remove")

- [ ] Unit tests

#### 5. Pinecone Node (`backend/nodes/storage/pinecone.py`)

- [ ] Pinecone integration:
  - Install pinecone-client
  - Connect to Pinecone
  - Create/use index

- [ ] Index management:
  - List existing indexes
  - Create new index (if needed)
  - Select existing index

- [ ] Namespace support:
  - Use namespace for organization
  - Optional namespace parameter

- [ ] Upsert vectors:
  - Batch upsert
  - Include metadata
  - Handle errors

- [ ] Output format:
  ```python
  {
      "index_name": str,
      "namespace": str,
      "vectors_upserted": int,
      "total_vectors": int
  }
  ```

- [ ] Configuration:
  - `api_key`: str (from env or input)
  - `index_name`: str
  - `namespace`: str (optional)
  - `create_index`: bool (default: False)
  - `dimension`: int (auto-detect)

- [ ] Cost tracking:
  - Track Pinecone usage
  - Estimate costs

- [ ] Unit tests with mocks

#### 6. Hybrid Search Node (`backend/nodes/retrieval/hybrid.py`)

- [ ] Combine vector + keyword search:
  - Perform vector search
  - Perform keyword search (BM25 or similar)
  - Combine results with weighted scoring

- [ ] Weighted scoring:
  - Vector weight (default: 0.7)
  - Keyword weight (default: 0.3)
  - Normalize scores
  - Re-rank results

- [ ] Output format:
  ```python
  {
      "results": List[Dict],
      "vector_results_count": int,
      "keyword_results_count": int,
      "combined_count": int
  }
  ```

- [ ] Configuration:
  - `vector_weight`: float (default: 0.7)
  - `keyword_weight`: float (default: 0.3)
  - `top_k`: int (default: 5)
  - `query`: str

- [ ] Unit tests

#### 7. Reranker Node (`backend/nodes/retrieval/reranker.py`)

- [ ] Cohere reranker:
  - Use Cohere rerank API
  - Re-rank search results
  - Return top-N results

- [ ] Cross-encoder support (optional):
  - Use sentence-transformers
  - Local reranking
  - Faster but less accurate

- [ ] Output format:
  ```python
  {
      "results": List[Dict],
      "input_count": int,
      "output_count": int,
      "score_improvements": List[float]
  }
  ```

- [ ] Configuration:
  - `model`: str (enum: "cohere", "cross-encoder")
  - `top_n`: int (default: 3)
  - `query`: str
  - `candidates`: List[Dict]  # from previous node

- [ ] Cost tracking:
  - Track Cohere API usage
  - Calculate costs

- [ ] Unit tests

#### 8. Anthropic Claude Node (`backend/nodes/llm/claude.py`)

- [ ] Claude API integration:
  - Use Anthropic SDK
  - Support Claude 3.5 Sonnet and Opus
  - Handle API responses

- [ ] Similar config to OpenAI:
  - `model`: str
  - `temperature`: float
  - `max_tokens`: int
  - `system_prompt`: str
  - `user_prompt_template`: str

- [ ] Output format:
  ```python
  {
      "response": str,
      "tokens_used": int,
      "cost": float
  }
  ```

- [ ] Cost tracking:
  - Track input/output tokens
  - Calculate cost based on model

- [ ] Unit tests with mocks

#### 9. Prompt Template Node (`backend/nodes/llm/prompt_template.py`)

- [ ] Template with variables:
  - Support `{variable}` syntax
  - Auto-detect variables
  - Validate template

- [ ] Variable detection:
  - Parse template string
  - Extract variable names
  - Validate required variables

- [ ] Preview rendering:
  - Render template with sample data
  - Show preview in API response

- [ ] Output format:
  ```python
  {
      "rendered_prompt": str,
      "variables_used": List[str],
      "variables_missing": List[str]
  }
  ```

- [ ] Configuration:
  - `template`: str (with {variables})
  - `variables`: Dict[str, Any] (optional, can come from inputs)

- [ ] Unit tests

---

### Backend: File Handling

#### 1. File Upload Service

- [ ] Handle multipart uploads:
  - Use FastAPI's `UploadFile`
  - Validate file types
  - Check file sizes

- [ ] Store files temporarily:
  - Save to `data/uploads/` directory
  - Generate unique filenames
  - Track file metadata

- [ ] Cleanup old files:
  - Scheduled cleanup job
  - Remove files older than X days
  - Handle cleanup errors

- [ ] File validation:
  - Check file extensions
  - Validate file content (magic numbers)
  - Enforce size limits

#### 2. Document Parsers

- [ ] PDF parser:
  - Use PyPDF2 or pdfplumber
  - Handle encrypted PDFs
  - Extract text and metadata

- [ ] DOCX parser:
  - Use python-docx
  - Extract text and formatting
  - Handle images (optional)

- [ ] Markdown parser:
  - Use markdown library
  - Preserve structure
  - Extract metadata (frontmatter)

- [ ] Text parser:
  - Handle various encodings
  - Detect encoding automatically
  - Extract basic metadata

---

### Backend: Advanced Features

#### 1. Parallel Execution

- [ ] Detect parallelizable nodes:
  - Analyze dependency graph
  - Find nodes that can run in parallel
  - Group by execution level

- [ ] Execute in parallel:
  - Use `asyncio.gather()` or `asyncio.create_task()`
  - Handle errors in parallel execution
  - Collect results

- [ ] Handle dependencies correctly:
  - Wait for dependencies
  - Pass outputs correctly
  - Maintain execution order where needed

#### 2. Caching

- [ ] Cache embeddings:
  - Cache key: text hash + model
  - Check cache before API call
  - Store in memory or Redis (optional)

- [ ] Cache LLM responses (optional):
  - Cache key: prompt hash + model + temperature
  - Configurable cache TTL
  - Invalidate on demand

- [ ] Cache node results:
  - Cache intermediate results
  - Invalidate on workflow change
  - Configurable cache size

#### 3. Retry Logic

- [ ] Configurable retries:
  - Per-node retry count
  - Global retry settings
  - Retry on specific errors

- [ ] Exponential backoff:
  - Increase delay between retries
  - Max retry delay
  - Jitter for distributed systems

- [ ] Error handling:
  - Log retry attempts
  - Track retry statistics
  - Fail after max retries

---

### Frontend: Enhanced Features

#### 1. File Upload UI

- [ ] Drag-and-drop file upload:
  - Drop zone component
  - Visual feedback
  - Multiple file support

- [ ] File preview:
  - Show file name and size
  - Show file type icon
  - Preview text content (optional)

- [ ] Progress indicator:
  - Upload progress bar
  - Show upload status
  - Handle upload errors

#### 2. Advanced Node Config

- [ ] Better form components:
  - Slider for numeric values
  - Code editor for templates
  - File picker for file inputs
  - Color picker (if needed)

- [ ] Slider components:
  - Range sliders
  - Value display
  - Step increments

- [ ] Code editor for templates:
  - Syntax highlighting
  - Variable autocomplete
  - Template validation

#### 3. Output Preview

- [ ] Expandable output views:
  - Collapsible sections
  - Show/hide full output
  - Scrollable content

- [ ] JSON viewer:
  - Pretty print JSON
  - Expand/collapse nodes
  - Search in JSON

- [ ] Text preview:
  - Syntax highlighting
  - Line numbers
  - Copy to clipboard

---

## ✅ Deliverables Checklist

- [ ] All MVP nodes implemented
- [ ] File uploads working
- [ ] Complete RAG pipeline functional
- [ ] Multiple storage options (FAISS, Pinecone)
- [ ] Advanced search options (Hybrid, Reranker)
- [ ] Multiple LLM options (OpenAI, Claude)
- [ ] Parallel execution working
- [ ] Caching implemented
- [ ] Retry logic working
- [ ] File upload UI functional
- [ ] Advanced node config UI
- [ ] Output preview working

---

## 🧪 Example Complete RAG Workflow

```json
{
  "nodes": [
    {
      "id": "1",
      "type": "upload_file",
      "data": {
        "file": "document.pdf"
      }
    },
    {
      "id": "2",
      "type": "pdf_parser",
      "data": {
        "extract_tables": true,
        "page_range": "all"
      }
    },
    {
      "id": "3",
      "type": "chunk",
      "data": {
        "chunk_size": 512,
        "chunk_overlap": 50
      }
    },
    {
      "id": "4",
      "type": "metadata_enricher",
      "data": {
        "auto_extract_dates": true,
        "add_source_filename": true
      }
    },
    {
      "id": "5",
      "type": "openai_embed",
      "data": {
        "model": "text-embedding-3-large"
      }
    },
    {
      "id": "6",
      "type": "pinecone_store",
      "data": {
        "index_name": "my-index",
        "namespace": "documents"
      }
    },
    {
      "id": "7",
      "type": "hybrid_search",
      "data": {
        "query": "What is the main topic?",
        "vector_weight": 0.7,
        "keyword_weight": 0.3,
        "top_k": 10
      }
    },
    {
      "id": "8",
      "type": "reranker",
      "data": {
        "model": "cohere",
        "top_n": 5
      }
    },
    {
      "id": "9",
      "type": "prompt_template",
      "data": {
        "template": "Context: {context}\n\nQuestion: {query}\n\nAnswer:"
      }
    },
    {
      "id": "10",
      "type": "claude_chat",
      "data": {
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7
      }
    }
  ],
  "edges": [
    {"source": "1", "target": "2"},
    {"source": "2", "target": "3"},
    {"source": "3", "target": "4"},
    {"source": "4", "target": "5"},
    {"source": "5", "target": "6"},
    {"source": "6", "target": "7"},
    {"source": "7", "target": "8"},
    {"source": "8", "target": "9"},
    {"source": "9", "target": "10"}
  ]
}
```

---

## 📝 Notes

- Prioritize nodes based on usage
- Test file uploads with various file types
- Handle large files gracefully
- Optimize parallel execution
- Monitor cache hit rates
- Document all new nodes

---

## 🔗 Related Files

- `backend/nodes/input/upload.py` - File upload node
- `backend/nodes/processing/pdf_parser.py` - PDF parser
- `backend/nodes/storage/pinecone.py` - Pinecone storage
- `backend/nodes/retrieval/hybrid.py` - Hybrid search
- `frontend/src/components/FileUpload/` - Upload UI

---

## ➡️ Next Phase

Once Phase 3 is complete, proceed to [Phase 4: Workflow Management](./PHASE_4_WORKFLOW_MANAGEMENT.md)

