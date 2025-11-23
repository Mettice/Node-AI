# Multi-Modal Support Implementation Plan

## Current State
- ✅ Text-only RAG (PDF, DOCX, TXT, MD)
- ✅ File upload system with file_id
- ✅ Node registry architecture
- ✅ BaseNode class for extensibility

## Implementation Plan

### Phase 1: Image Support (Priority: High)

#### A. Image Upload & Processing
**Backend:**
1. **Extend File Upload API** (`backend/api/files.py`)
   - Add image extensions: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`
   - Store images in `uploads/` directory
   - Return image metadata (dimensions, format, size)

2. **Image Input Node** (`backend/nodes/input/image_loader.py`)
   - Load image from file_id
   - Extract image metadata
   - Output: image_path, metadata, base64_encoded (optional)

3. **OCR Node** (`backend/nodes/processing/ocr.py`)
   - Extract text from images using Tesseract or Google Vision API
   - Config: language, OCR engine (tesseract/google)
   - Output: extracted_text, confidence_scores

4. **Vision Node** (`backend/nodes/llm/vision.py`)
   - GPT-4 Vision API integration
   - Image description/analysis
   - Config: model, prompt, max_tokens
   - Output: description, analysis

**Frontend:**
- Update `FileUpload` component to accept images
- Add image preview in file list
- Create ImageLoader node UI
- Create OCR node UI
- Create Vision node UI

**Dependencies:**
```txt
pytesseract>=0.3.10
Pillow>=10.0.0
google-cloud-vision>=3.4.0  # Optional
openai>=1.0.0  # For GPT-4 Vision
```

#### B. Workflow Examples
```
Image Upload → Image Loader → OCR → Chunk → Embed → Store
Image Upload → Image Loader → Vision → Chunk → Embed → Store
Image Upload → Image Loader → OCR + Vision → Merge → Embed → Store
```

---

### Phase 2: Audio/Video Support (Priority: Medium)

#### A. Audio Processing
**Backend:**
1. **Extend File Upload API**
   - Add audio extensions: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`
   - Add video extensions: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`

2. **Audio Loader Node** (`backend/nodes/input/audio_loader.py`)
   - Load audio file
   - Extract metadata (duration, format, sample_rate)
   - Output: audio_path, metadata

3. **Transcription Node** (`backend/nodes/processing/transcribe.py`)
   - Whisper API integration (OpenAI or local)
   - Config: model (tiny/base/small/medium/large), language
   - Output: transcript, segments, timestamps

4. **Video Frame Extractor Node** (`backend/nodes/processing/video_frames.py`)
   - Extract frames from video
   - Config: fps, frame_count, resolution
   - Output: frames (as images), timestamps

**Frontend:**
- Update file upload for audio/video
- Audio/video preview components
- Transcription node UI
- Video frame extractor UI

**Dependencies:**
```txt
openai-whisper>=20231117  # For local transcription
ffmpeg-python>=0.2.0  # For video processing
moviepy>=1.0.3  # Alternative video processing
```

#### B. Workflow Examples
```
Audio Upload → Audio Loader → Transcribe → Chunk → Embed → Store
Video Upload → Video Loader → Frame Extractor → Vision → Chunk → Embed → Store
Video Upload → Video Loader → Extract Audio → Transcribe → Chunk → Embed → Store
```

---

### Phase 3: Structured Data Support (Priority: Medium)

#### A. Data Processing
**Backend:**
1. **Extend File Upload API**
   - Add data extensions: `.csv`, `.xlsx`, `.json`, `.parquet`

2. **Data Loader Node** (`backend/nodes/input/data_loader.py`)
   - Load CSV, Excel, JSON files
   - Parse and validate structure
   - Output: data (dict/list), schema, metadata

3. **Data to Text Node** (`backend/nodes/processing/data_to_text.py`)
   - Convert structured data to natural language
   - Config: format (table, list, narrative)
   - Output: text representation

4. **Database Query Node** (`backend/nodes/input/db_query.py`)
   - Execute SQL queries
   - Config: connection_string, query, parameters
   - Output: results (rows), schema

5. **API Data Node** (`backend/nodes/input/api_data.py`)
   - Fetch data from REST APIs
   - Config: url, method, headers, params, body
   - Output: response_data, status_code

**Frontend:**
- Data file upload support
- Data preview (table view for CSV/Excel)
- Database query builder UI
- API configuration UI

**Dependencies:**
```txt
pandas>=2.0.0  # For CSV/Excel processing
openpyxl>=3.1.0  # For Excel files
sqlalchemy>=2.0.0  # For database queries
httpx>=0.25.0  # For API calls
```

#### B. Workflow Examples
```
CSV Upload → Data Loader → Data to Text → Chunk → Embed → Store
Database → DB Query → Data to Text → Chunk → Embed → Store
API → API Data → Data to Text → Chunk → Embed → Store
```

---

## Implementation Order

### Week 1: Image Support Foundation
1. ✅ Extend file upload API for images
2. ✅ Create ImageLoader node
3. ✅ Create OCR node (Tesseract)
4. ✅ Create Vision node (GPT-4 Vision)
5. ✅ Update frontend for image support

### Week 2: Audio/Video Support
1. ✅ Extend file upload for audio/video
2. ✅ Create AudioLoader node
3. ✅ Create Transcription node (Whisper)
4. ✅ Create VideoFrameExtractor node
5. ✅ Update frontend for audio/video

### Week 3: Structured Data Support
1. ✅ Extend file upload for data files
2. ✅ Create DataLoader node
3. ✅ Create DataToText node
4. ✅ Create DatabaseQuery node
5. ✅ Create APIData node
6. ✅ Update frontend for data support

---

## Node Categories

### New Categories to Add:
- `vision` - Vision/Image processing nodes
- `audio` - Audio processing nodes
- `video` - Video processing nodes
- `data` - Structured data nodes

### Updated Categories:
- `input` - Now includes: text, file, image, audio, video, data, db, api
- `processing` - Now includes: chunk, ocr, transcribe, video_frames, data_to_text

---

## File Structure

```
backend/nodes/
├── input/
│   ├── image_loader.py      # NEW
│   ├── audio_loader.py      # NEW
│   ├── video_loader.py      # NEW
│   ├── data_loader.py       # NEW
│   ├── db_query.py          # NEW
│   └── api_data.py          # NEW
├── processing/
│   ├── ocr.py               # NEW
│   ├── transcribe.py        # NEW
│   ├── video_frames.py      # NEW
│   └── data_to_text.py      # NEW
└── llm/
    └── vision.py            # NEW
```

---

## Testing Strategy

1. **Unit Tests**: Each new node type
2. **Integration Tests**: Multi-modal workflows
3. **E2E Tests**: Complete pipelines (Image → OCR → Embed → Search)
4. **Performance Tests**: Large files, batch processing

---

## Future Enhancements

1. **Multi-modal Embeddings**: CLIP for image embeddings
2. **Video Analysis**: Scene detection, object tracking
3. **Real-time Processing**: Streaming audio/video
4. **Batch Processing**: Process multiple files at once
5. **Custom Models**: Support for custom OCR/Vision models

