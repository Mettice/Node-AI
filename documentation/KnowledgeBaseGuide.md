# Knowledge Base System Guide

## Overview

The Knowledge Base system allows you to upload documents, process them (chunk, embed, and store in a vector database), and then use them in workflows for RAG (Retrieval-Augmented Generation) operations.

## How It Works

### 1. **Create a Knowledge Base**
   - Click "New Knowledge Base" in the Knowledge Base Manager
   - Enter a name and optional description
   - This creates an empty container for your documents

### 2. **Upload Files**
   - **Two ways to upload files:**
     1. **From the Process Modal** (Easiest):
        - Click "Process" button on your knowledge base card
        - Click "Upload File" button in the modal
        - Select your file(s) - they'll be uploaded and automatically selected
     2. **Separate File Upload** (Alternative):
        - Use the File Upload feature separately
        - Then select those files when processing
   
   - **Supported formats:**
     - Documents: PDF, DOCX, TXT, MD, DOC
     - Images: JPG, PNG, GIF, WEBP, BMP
     - Audio: MP3, WAV, M4A, OGG, FLAC
     - Video: MP4, AVI, MOV, MKV, WEBM
     - Data: CSV, XLSX, JSON, PARQUET
   - Maximum file size: 50MB

### 3. **Process Files into Knowledge Base**
   - Click "Process" button on your knowledge base card
   - Select the files you want to process (from previously uploaded files)
   - Choose versioning option:
     - **Create New Version**: Keeps existing version, creates new one
     - **Replace Current Version**: Replaces current version (old one deprecated)
   - Optionally customize processing configuration:
     - **Chunking**: How documents are split (chunk size, overlap, strategy)
     - **Embedding**: Which embedding model to use (OpenAI, etc.)
     - **Vector Store**: Where to store vectors (FAISS, Pinecone, etc.)
   - Click "Start Processing"

### 4. **Processing Pipeline**
   When you process files, the system:
   1. **Loads** files and extracts text
   2. **Chunks** text into smaller pieces (based on chunk config)
   3. **Creates embeddings** for each chunk (using embedding model)
   4. **Stores** embeddings in vector database
   5. **Tracks** processing status, costs, and metadata

### 5. **Use in Workflows**
   - Knowledge bases can be used in workflows via the `vector_search` node
   - The node queries the vector store to find relevant chunks
   - These chunks are then used as context for LLM operations

## Key Concepts

### **Versions**
- Each knowledge base can have multiple versions
- Versions allow you to:
  - Keep history of changes
  - Rollback to previous versions
  - Compare different versions
  - A/B test different processing configurations

### **Processing Status**
- **Pending**: Processing hasn't started yet
- **Processing**: Currently being processed
- **Completed**: Successfully processed and ready to use
- **Failed**: Processing encountered an error

### **Configuration**
- **Chunk Config**: How documents are split
  - `chunk_size`: Size of each chunk (default: 512)
  - `chunk_overlap`: Overlap between chunks (default: 50)
  - `strategy`: Chunking strategy (recursive, etc.)
  
- **Embed Config**: Embedding model settings
  - `provider`: Embedding provider (openai, etc.)
  - `model`: Specific model (text-embedding-3-small, etc.)
  
- **Vector Store Config**: Vector database settings
  - `provider`: Vector store provider (faiss, pinecone, etc.)
  - `index_type`: Type of index (flat, etc.)

## Workflow

```
1. Create Knowledge Base
   ↓
2. Upload Files (via File Upload API/UI)
   ↓
3. Process Files (select files, configure, start processing)
   ↓
4. Wait for Processing (check status in detail view)
   ↓
5. Use in Workflows (via vector_search node)
```

## Common Issues

### "No files available" when processing
- **Solution**: Upload files first using the File Upload feature
- Files must be uploaded before they can be selected for processing

### Rate Limiting (429 errors)
- **Solution**: The system polls for status updates
- If you see rate limit errors, wait a moment and refresh
- Rate limits: 60 requests/minute for detail view, 30/minute for list

### Processing Failed
- Check the processing log in the version details
- Common causes:
  - Invalid file format
  - File too large
  - API key issues (for embedding models)
  - Insufficient permissions

## Best Practices

1. **Organize by Topic**: Create separate knowledge bases for different topics
2. **Version Control**: Use versions to track changes and experiment
3. **Monitor Costs**: Processing costs are tracked per version
4. **Test Configurations**: Try different chunk sizes and embedding models
5. **Regular Updates**: Process new files as they become available

## API Endpoints

- `POST /api/v1/knowledge-bases` - Create knowledge base
- `GET /api/v1/knowledge-bases` - List all knowledge bases
- `GET /api/v1/knowledge-bases/{kb_id}` - Get knowledge base details
- `POST /api/v1/knowledge-bases/{kb_id}/process` - Process files
- `GET /api/v1/knowledge-bases/{kb_id}/versions` - List versions
- `POST /api/v1/knowledge-bases/{kb_id}/versions/{version}/rollback` - Rollback to version
- `GET /api/v1/files/upload` - Upload files
- `GET /api/v1/files/list` - List uploaded files

