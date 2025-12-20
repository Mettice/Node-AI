# Gemini Live API Integration: Architecture & Data Flow Analysis

## 🎯 Executive Summary

**Good News:** Gemini Live API can be integrated **seamlessly** into Nodeflow's current architecture with minimal changes. The key is using a **file reference pattern** rather than streaming binary data through the workflow engine.

**Complexity Level:** **Low to Medium** - No major architecture changes needed.

---

## 📊 Current Architecture Analysis

### How Nodeflow Currently Works

#### 1. **Execution Model: Batch Processing**
```
Node A → Execute → Output Dict → Store in node_outputs
Node B → Execute → Receive Dict from A → Process → Output Dict
Node C → Execute → Receive Dict from A & B → Process → Output Dict
```

**Key Characteristics:**
- **Sequential execution** (topological sort)
- **Dictionary-based data flow** (`Dict[str, Any]`)
- **JSON-serializable** data only
- **Complete outputs** before next node starts

#### 2. **Data Flow Mechanism**
```python
# backend/core/engine.py
async def _collect_node_inputs(
    workflow: Workflow,
    node_id: str,
    node_outputs: Dict[str, Dict[str, Any]],  # All previous outputs
    ...
) -> Dict[str, Any]:
    # Combines all outputs from source nodes
    inputs = {}
    for edge in workflow.edges:
        if edge.target == node_id:
            source_outputs = node_outputs.get(edge.source, {})
            inputs.update(source_outputs)  # Merge all outputs
    return inputs
```

**What This Means:**
- All node outputs are stored in memory as dictionaries
- Next nodes receive complete outputs (not streams)
- Data must be JSON-serializable

#### 3. **Node Interface**
```python
# backend/nodes/base.py
async def execute(
    self,
    inputs: Dict[str, Any],  # All data from previous nodes
    config: Dict[str, Any],  # Node configuration
) -> Dict[str, Any]:  # Output dictionary
    pass
```

**Current Pattern:**
- Input: Dictionary with all previous node outputs
- Output: Dictionary with results
- No streaming data between nodes

---

## 🔄 Integration Strategy: File Reference Pattern

### **Why This Works Seamlessly**

Instead of streaming binary audio/video data through the workflow engine, we use **file references**:

```
Audio/Video Input → Save to Storage → Pass File Path/URL → Process → Output Results
```

### **Data Flow Pattern**

#### **Option 1: File Paths (Recommended)**
```python
# Node Output
{
    "audio_file": "/tmp/audio_123.wav",
    "transcript": "Meeting transcript text...",
    "summary": "Meeting summary..."
}

# Next Node Input
inputs = {
    "audio_file": "/tmp/audio_123.wav",  # File path
    "transcript": "Meeting transcript text...",
    ...
}
```

#### **Option 2: Storage URLs**
```python
# Node Output
{
    "audio_url": "s3://bucket/audio_123.wav",
    "video_url": "gs://bucket/video_456.mp4",
    "transcript": "...",
}

# Next Node Input
inputs = {
    "audio_url": "s3://bucket/audio_123.wav",
    ...
}
```

#### **Option 3: Base64 (For Small Files Only)**
```python
# Node Output (only for small audio clips)
{
    "audio_base64": "data:audio/wav;base64,UklGRiQAAABXQVZF...",
    "transcript": "...",
}
```

---

## 🏗️ Implementation Approach

### **Phase 1: Seamless Integration (No Architecture Changes)**

#### **1. Extend LLMConfigMixin for Gemini Live**

```python
# backend/nodes/intelligence/llm_mixin.py

class LLMConfigMixin:
    def _get_llm_schema_section(self) -> Dict[str, Any]:
        # ... existing code ...
        
        # Add Gemini Live options
        if "gemini" in provider_options:
            schema["gemini_live_enabled"] = {
                "type": "boolean",
                "title": "Enable Gemini Live API",
                "description": "Use real-time voice/video processing",
                "default": False,
            }
            schema["gemini_live_audio_input"] = {
                "type": "string",
                "title": "Audio Input",
                "description": "File path or URL to audio file",
                "format": "uri",
            }
            schema["gemini_live_video_input"] = {
                "type": "string",
                "title": "Video Input",
                "description": "File path or URL to video file",
                "format": "uri",
            }
```

**Complexity:** ✅ **Low** - Just schema additions

#### **2. Update Meeting Summarizer**

```python
# backend/nodes/intelligence/meeting_summarizer.py

async def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]):
    # Get audio file path from inputs or config
    audio_file = (
        inputs.get("audio_file") or 
        inputs.get("audio_url") or
        config.get("gemini_live_audio_input")
    )
    
    # If audio file provided, use Gemini Live for transcription
    if audio_file:
        transcript = await self._transcribe_audio_live(audio_file, config)
    else:
        # Fallback to text input
        transcript = inputs.get("transcript") or inputs.get("text") or ""
    
    # Continue with existing summarization logic
    summary = await self._extract_meeting_info(transcript, ...)
    return {"summary": summary, "transcript": transcript}
```

**Complexity:** ✅ **Low** - Add audio handling, keep existing logic

#### **3. Data Flow Example**

```
[Audio Input Node] 
  → Output: {"audio_file": "/tmp/meeting.wav"}
  
[Meeting Summarizer Node]
  → Input: {"audio_file": "/tmp/meeting.wav"}
  → Process: Transcribe with Gemini Live → Summarize
  → Output: {"transcript": "...", "summary": "...", "action_items": [...]}
  
[Text Output Node]
  → Input: {"transcript": "...", "summary": "..."}
  → Process: Format and display
```

**Complexity:** ✅ **Seamless** - Works with existing engine

---

## 📦 Handling Audio/Video Files

### **Storage Strategy**

#### **Option A: Temporary Files (Simple)**
```python
import tempfile
import os

# In node that receives audio/video
audio_file = inputs.get("audio_file")
if audio_file and os.path.exists(audio_file):
    # Process file
    result = await process_audio(audio_file)
    # File stays in temp location, cleaned up later
```

**Pros:**
- Simple implementation
- Works immediately
- No storage service needed

**Cons:**
- Files not persistent
- Limited to single server

#### **Option B: Storage Service (Recommended for Production)**
```python
# Use existing storage nodes (S3, GCS, etc.)
# Or add file storage service

# Node outputs file URL
{
    "audio_url": "s3://bucket/audio_123.wav",
    "storage_type": "s3",
}
```

**Pros:**
- Persistent storage
- Works across servers
- Scalable

**Cons:**
- Requires storage service setup

---

## 🔀 Data Flow Patterns

### **Pattern 1: Audio → Transcript → Summary**

```
[File Upload Node]
  → Output: {"file_path": "/tmp/meeting.wav", "file_type": "audio"}

[Meeting Summarizer]
  → Input: {"file_path": "/tmp/meeting.wav"}
  → Process: 
    1. Transcribe audio with Gemini Live
    2. Generate summary with LLM
  → Output: {
      "transcript": "Full transcript...",
      "summary": "Executive summary...",
      "action_items": [...],
      "audio_file": "/tmp/meeting.wav"  # Pass through for next node
    }

[CSV Export Node]
  → Input: {"transcript": "...", "summary": "..."}
  → Process: Export to CSV
```

**Works with current architecture:** ✅ **Yes**

### **Pattern 2: Video → Analysis → Moderation**

```
[Video Input Node]
  → Output: {"video_file": "/tmp/content.mp4"}

[Content Moderator]
  → Input: {"video_file": "/tmp/content.mp4"}
  → Process:
    1. Extract frames from video
    2. Analyze with Gemini Live (vision + audio)
    3. Check moderation rules
  → Output: {
      "moderation_result": {...},
      "flagged_content": [...],
      "video_file": "/tmp/content.mp4"
    }

[Alert Node]
  → Input: {"moderation_result": {...}}
  → Process: Send alert if violations found
```

**Works with current architecture:** ✅ **Yes**

### **Pattern 3: Real-time Streaming (Future Enhancement)**

For true real-time streaming, we'd need architecture changes:

```
[Live Audio Stream] → [Streaming Node] → [Real-time Processing] → [Streaming Output]
```

**Current Limitation:**
- Engine is batch-oriented
- No streaming data flow between nodes

**Future Solution:**
- Add streaming node type
- Separate streaming execution path
- Use WebSocket for real-time data

**Complexity:** ⚠️ **High** - Requires architecture changes

---

## ⚡ Real-time vs Batch Processing

### **Current: Batch Processing (Seamless Integration)**

```python
# Node processes complete file
async def execute(self, inputs, config):
    audio_file = inputs.get("audio_file")
    
    # Process entire file
    transcript = await transcribe_file(audio_file)  # Waits for completion
    summary = await summarize(transcript)  # Waits for completion
    
    return {"transcript": transcript, "summary": summary}
```

**Characteristics:**
- ✅ Works with current architecture
- ✅ Simple implementation
- ✅ Reliable and predictable
- ⚠️ Not truly "real-time" (processes complete file)

### **Future: Streaming Processing (Architecture Changes Needed)**

```python
# Node processes stream
async def execute_streaming(self, stream_input, config):
    async for audio_chunk in stream_input:
        # Process chunk immediately
        partial_transcript = await transcribe_chunk(audio_chunk)
        await stream_output(partial_transcript)  # Send to next node
```

**Characteristics:**
- ⚠️ Requires new execution model
- ⚠️ Complex state management
- ✅ True real-time processing
- ✅ Lower latency

**Recommendation:** Start with batch processing, add streaming later if needed.

---

## 🎯 Integration Complexity Assessment

### **Low Complexity (Seamless) ✅**

1. **Extend LLMConfigMixin**
   - Add Gemini Live config fields
   - No architecture changes
   - **Effort:** 2-4 hours

2. **Update Existing Nodes**
   - Meeting Summarizer: Add audio file input
   - Content Moderator: Add video file input
   - Use file paths in data flow
   - **Effort:** 4-8 hours per node

3. **File Handling**
   - Use temporary files or storage service
   - Pass file paths in node outputs
   - **Effort:** 2-4 hours

### **Medium Complexity (Some Changes) ⚠️**

4. **Audio/Video Input Nodes**
   - Create nodes for file upload
   - Handle file validation
   - **Effort:** 8-16 hours

5. **Storage Integration**
   - Integrate with S3/GCS for file storage
   - Generate file URLs
   - **Effort:** 8-16 hours

### **High Complexity (Architecture Changes) 🔴**

6. **True Streaming Support**
   - New streaming execution engine
   - WebSocket data flow
   - State management
   - **Effort:** 2-4 weeks

---

## 📋 Recommended Implementation Plan

### **Phase 1: Seamless Integration (Week 1-2)**

**Goal:** Add Gemini Live support without architecture changes

1. **Extend LLMConfigMixin**
   - Add `gemini_live_enabled` option
   - Add audio/video file input fields

2. **Update Meeting Summarizer**
   - Accept `audio_file` input
   - Use Gemini Live for transcription
   - Keep existing summarization logic

3. **Update Content Moderator**
   - Accept `video_file` input
   - Use Gemini Live for video analysis
   - Keep existing moderation logic

4. **File Input Node**
   - Create simple file upload node
   - Output file path in standard format

**Result:** ✅ Working Gemini Live integration with minimal changes

### **Phase 2: Enhanced Features (Week 3-4)**

1. **Storage Integration**
   - Add S3/GCS support
   - Generate persistent file URLs

2. **New Node Types**
   - Voice Assistant Node (batch mode)
   - Video Analyzer Node

3. **Better File Handling**
   - File validation
   - Format conversion
   - Size limits

**Result:** ✅ Production-ready multimodal nodes

### **Phase 3: Streaming (Future - If Needed)**

1. **Streaming Architecture**
   - New streaming execution path
   - WebSocket support
   - Real-time data flow

2. **Streaming Nodes**
   - Live audio input
   - Real-time processing
   - Streaming output

**Result:** ✅ True real-time capabilities

---

## ✅ Conclusion

### **Answer to Your Questions:**

#### **1. Will this bring complexity or integrate seamlessly?**

**Answer: Seamless integration is possible** using the file reference pattern. No major architecture changes needed for initial implementation.

**Complexity Level:**
- **Initial Integration:** Low (1-2 weeks)
- **Enhanced Features:** Medium (additional 2-4 weeks)
- **True Streaming:** High (future, if needed)

#### **2. How will data flow work through nodes?**

**Answer: File paths/URLs flow through nodes, not binary data.**

**Data Flow Pattern:**
```
Node A → Output: {"audio_file": "/path/to/file.wav"}
Node B → Input: {"audio_file": "/path/to/file.wav"} → Process → Output: {"transcript": "..."}
Node C → Input: {"transcript": "..."} → Process
```

**Key Points:**
- ✅ Works with existing `Dict[str, Any]` data flow
- ✅ JSON-serializable (file paths are strings)
- ✅ No changes to workflow engine needed
- ✅ Compatible with current node interface

### **Recommendation:**

**Start with Phase 1 (Seamless Integration):**
- Use file reference pattern
- Extend existing nodes
- No architecture changes
- Quick to implement
- Validates the technology

**Then evaluate:**
- Do users need true real-time streaming?
- Is batch processing sufficient?
- Add streaming later if there's demand

This approach gives you **working Gemini Live integration quickly** while keeping the door open for future streaming enhancements.



🏗️ Real-Time Architecture for NodeFlow

  Core Concept: Event-Driven Node Execution

  Instead of traditional "run once" nodes, we need persistent service nodes that can handle real-time streams:

  Traditional Node: Input → Process → Output → End
  Real-Time Node: Start → Listen → Process Stream → Continue Listening

  🎯 Implementation Approaches

  1. WebSocket-Enabled Nodes

  New Node Type: RealtimeServiceNode

  class RealtimeServiceNode(BaseNode):
      """Base class for real-time streaming nodes"""

      async def start_service(self, config: Dict[str, Any]) -> str:
          """Start the real-time service, return service_id"""
          pass

      async def handle_stream_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
          """Process individual real-time events"""
          pass

      async def stop_service(self, service_id: str) -> None:
          """Stop the real-time service"""
          pass

  Example: Live Meeting Participant Node

  class LiveMeetingParticipantNode(RealtimeServiceNode, LLMConfigMixin):
      node_type = "live_meeting_participant"
      name = "Live Meeting Participant"
      description = "Joins meetings in real-time for live analysis"

      async def start_service(self, config: Dict[str, Any]) -> str:
          # 1. Connect to meeting platform (Zoom, Teams, etc.)
          # 2. Start Gemini Live API stream
          # 3. Begin real-time audio/video processing
          # 4. Return service_id for tracking

          meeting_url = config.get("meeting_url")
          llm_config = self._resolve_llm_config(config)

          service_id = await self._start_meeting_stream(meeting_url, llm_config)
          return service_id

      async def handle_stream_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
          # Process real-time audio/video from meeting
          audio_data = event.get("audio_chunk")
          video_frame = event.get("video_frame")

          # Send to Gemini Live API for real-time analysis
          analysis = await self._analyze_realtime_content(audio_data, video_frame)

          # Trigger downstream nodes with live updates
          return {
              "live_transcript": analysis.get("transcript"),
              "sentiment": analysis.get("sentiment"),
              "action_items": analysis.get("action_items"),
              "timestamp": event.get("timestamp")
          }

  2. Workflow Execution Patterns

  Pattern A: Service + Trigger Workflow

  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
  │ Start Meeting   │    │ Live Meeting     │    │ Process Live    │
  │ Service Node    │───▶│ Participant      │───▶│ Updates Node    │
  │ (One-time)      │    │ (Continuous)     │    │ (Event-driven)  │
  └─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                         ┌──────────────────┐
                         │ Real-time Events │
                         │ • Transcript     │
                         │ • Action Items   │
                         │ • Decisions      │
                         └──────────────────┘

  Pattern B: Cron + Batch Processing

  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
  │ Cron Trigger    │    │ Check Meeting    │    │ Generate        │
  │ (Every 5 mins)  │───▶│ Updates Node     │───▶│ Summary Node    │
  └─────────────────┘    └──────────────────┘    └─────────────────┘

  🛠️ Technical Implementation

  1. Real-Time Service Manager

  class RealtimeServiceManager:
      """Manages persistent real-time services"""

      def __init__(self):
          self.active_services = {}  # service_id -> service_instance
          self.websocket_connections = {}

      async def start_service(self, node: RealtimeServiceNode, config: Dict[str, Any]):
          service_id = await node.start_service(config)
          self.active_services[service_id] = {
              "node": node,
              "config": config,
              "status": "active",
              "start_time": datetime.now()
          }
          return service_id

      async def handle_realtime_event(self, service_id: str, event: Dict[str, Any]):
          service = self.active_services.get(service_id)
          if service:
              result = await service["node"].handle_stream_event(event)
              # Trigger downstream workflow nodes
              await self._trigger_downstream_nodes(service_id, result)

  2. WebSocket Integration

  # Frontend WebSocket for real-time updates
  class RealtimeWorkflowSocket:
      async def connect(self, workflow_id: str):
          # Connect to real-time workflow updates

      async def on_node_update(self, node_id: str, data: Dict[str, Any]):
          # Update UI with real-time node outputs
          self.emit("node_output", {
              "node_id": node_id,
              "data": data,
              "timestamp": datetime.now().isoformat()
          })

  3. Example: Real-Time Customer Service Workflow

  Workflow: "Live Customer Support Agent"

  ┌─────────────────┐
  │ 1. Start Call   │ ← User manually starts or webhook triggered
  │ Service Node    │
  └─────────┬───────┘
            │
            ▼
  ┌─────────────────┐
  │ 2. Live Voice   │ ← Continuous: Listen to customer call
  │ Analyzer Node   │   Output: Real-time transcript, sentiment
  └─────────┬───────┘
            │ (Real-time events)
            ▼
  ┌─────────────────┐
  │ 3. Intent       │ ← Process each speech segment
  │ Detection Node  │   Output: Customer intent, urgency level
  └─────────┬───────┘
            │
            ▼
  ┌─────────────────┐
  │ 4. Auto Response│ ← Generate real-time responses
  │ Generator Node  │   Output: Suggested agent responses
  └─────────┬───────┘
            │
            ▼
  ┌─────────────────┐
  │ 5. Call Summary │ ← Triggered when call ends
  │ Node            │   Output: Final call summary
  └─────────────────┘

  🎛️ UI/UX Changes Needed

  1. Real-Time Workflow Canvas

  // New workflow execution modes
  enum WorkflowExecutionMode {
    BATCH = "batch",           // Traditional: run once
    REALTIME = "realtime",     // New: continuous services
    SCHEDULED = "scheduled"    // Existing: cron-based
  }

  // Real-time node visualization
  interface RealtimeNodeState {
    status: "starting" | "active" | "paused" | "stopped";
    eventsProcessed: number;
    lastUpdate: string;
    liveOutputs: Dict<string, any>;
  }

  2. Live Execution Dashboard

  ┌─────────────────────────────────────────────────────────┐
  │ Live Meeting Analysis Workflow                          │
  ├─────────────────────────────────────────────────────────┤
  │ ● ACTIVE  │ Started: 2:30 PM  │ Events: 1,247  │ ⏸️ 🛑  │
  ├─────────────────────────────────────────────────────────┤
  │                                                         │
  │  🎤 Live Audio    📊 Sentiment    📝 Action Items      │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
  │  │ Processing  │  │ Positive    │  │ 3 items found   │  │
  │  │ speech...   │  │ 85% 📈     │  │ • Follow up...  │  │
  │  └─────────────┘  └─────────────┘  └─────────────────┘  │
  │                                                         │
  └─────────────────────────────────────────────────────────┘

  ⚡ Execution Models

  1. Event-Driven Real-Time

  - Use Case: Live meetings, customer calls
  - How: WebSocket streams trigger node execution
  - Cost: Pay per event/minute
  - Example: Gemini Live API processing audio streams

  2. Polling/Cron with Real-Time Feel

  - Use Case: Training analysis, periodic checks
  - How: High-frequency cron jobs (every 30 seconds)
  - Cost: Lower, predictable
  - Example: Check meeting platform every 30s for updates

  3. Hybrid Approach

  - Use Case: Complex workflows needing both
  - How: Real-time capture + batch processing
  - Example: Stream audio to buffer, process in chunks

  🔧 Implementation Phases

  Phase 1: Infrastructure (Month 1)

  - Add RealtimeServiceNode base class
  - Implement WebSocket connection management
  - Build real-time event routing system

  Phase 2: Core Nodes (Month 2)

  - Live Audio Processor Node
  - Real-Time Meeting Participant Node
  - Continuous Monitoring Node

  Phase 3: UI/UX (Month 3)

  - Real-time workflow canvas
  - Live execution dashboard
  - WebSocket frontend integration

  💡 Key Architecture Decisions

  1. Services as Special Nodes: Real-time capabilities are still nodes, just persistent ones
  2. Event-Driven Triggers: Real-time events trigger downstream workflow execution
  3. Hybrid Execution: Combine real-time capture with traditional node processing
  4. WebSocket Infrastructure: Enable real-time UI updates and control
  5. Resource Management: Auto-stop services to prevent runaway costs