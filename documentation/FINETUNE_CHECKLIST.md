# Fine-Tuning Feature Checklist

## Overview
Complete fine-tuning workflow: Upload dataset → Train → Deploy → Use in workflows

**Why it matters:** Unlocks domain-specific intelligence (legal, finance, pharma) and gives builders full control over their AI models.

---

## ✅ Phase 1: Fine-Tune Node (Core Implementation)

### Backend
- [x] **Fine-Tune Node Core** - Start training job, return job_id
- [x] **Training Data Support** - Accept data from file upload (JSONL)
- [x] **Training Data Support** - Accept data from previous node (array input)
- [x] **Data Validation** - Validate JSONL format (messages or prompt/completion)
- [x] **Validation Split** - Support train/validation split (0-100%)
- [x] **OpenAI Integration** - Upload files, create fine-tuning job
- [x] **Cost Estimation** - Calculate estimated training cost
- [x] **Error Handling** - Proper error messages and cleanup
- [x] **Node Registration** - Registered in node registry

### Frontend
- [x] **Node Type Registration** - Added to WorkflowCanvas nodeTypes
- [x] **Icon & Styling** - GraduationCap icon, training category color
- [x] **Node Card** - Added to sidebar with proper icon
- [x] **Configuration Schema** - Schema defined for all parameters

### Configuration Options
- [x] Provider selection (OpenAI, Anthropic, Custom)
- [x] Base model selection (gpt-3.5-turbo, gpt-4, etc.)
- [x] Training file ID (optional, for file upload)
- [x] Validation split (0.0 to 1.0)
- [x] Epochs (1-50)
- [x] Batch size (optional, auto)
- [x] Learning rate (optional, auto)

---

## 🔄 Phase 2: Async Job Management

### Status Checking
- [ ] **Status API Endpoint** - `/api/v1/finetune/{job_id}/status`
  - Check job status (validating, queued, running, succeeded, failed)
  - Get progress percentage
  - Get time remaining estimate
  - Get current cost

- [ ] **Background Polling Service** - Poll OpenAI API every 5 minutes
  - Update job status in database
  - Stream status updates via SSE
  - Auto-resume workflow when complete

- [ ] **Job Storage** - Store job metadata in database
  - Job ID, status, progress, cost
  - Training parameters
  - Created/updated timestamps

### Visual Feedback
- [ ] **Node Status Display** - Show job status on node
  - Gray: Not started
  - Blue (animated): Uploading data
  - Yellow (pulsing): Training (with progress %)
  - Green: Training complete
  - Red: Training failed

- [ ] **Progress Bar** - Real-time progress display
  - Progress percentage
  - Time remaining estimate
  - Cost so far

- [ ] **SSE Events** - Stream job status updates
  - `finetune_job_started`
  - `finetune_job_progress` (with %)
  - `finetune_job_completed` (with model ID)
  - `finetune_job_failed` (with error)

---

## 📦 Phase 3: Model Registry

### Database Schema
- [ ] **Models Table** - Store fine-tuned models
  - `id` (UUID)
  - `job_id` (OpenAI job ID)
  - `model_id` (OpenAI model ID, e.g., `ft:gpt-3.5-turbo:org:model:id`)
  - `name` (user-friendly name)
  - `description` (optional)
  - `base_model` (e.g., `gpt-3.5-turbo`)
  - `provider` (openai, anthropic, custom)
  - `status` (training, ready, failed, deleted)
  - `training_examples` (count)
  - `validation_examples` (count)
  - `epochs` (number)
  - `cost` (actual cost)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
  - `metadata` (JSON, training params, etc.)

- [ ] **Model Versions** - Track model versions
  - `version` (integer, auto-increment)
  - `model_id` (parent model)
  - `created_at`
  - `notes` (changelog)

- [ ] **Model Usage** - Track usage statistics
  - `model_id`
  - `used_at` (timestamp)
  - `node_type` (embed, chat, etc.)
  - `execution_id` (optional)

### API Endpoints
- [ ] **List Models** - `GET /api/v1/models`
  - Filter by status, provider, base_model
  - Pagination support
  - Sort by created_at, name, usage_count

- [ ] **Get Model** - `GET /api/v1/models/{model_id}`
  - Full model details
  - Usage statistics
  - Version history

- [ ] **Delete Model** - `DELETE /api/v1/models/{model_id}`
  - Soft delete (mark as deleted)
  - Option to delete from OpenAI

- [ ] **Update Model** - `PATCH /api/v1/models/{model_id}`
  - Update name, description
  - Add tags/categories

### Frontend Panel
- [ ] **Model Registry Component** - Sidebar panel
  - List all models with status badges
  - Filter/search functionality
  - Sort options
  - Model cards showing:
    - Name, base model, provider
    - Status (with color coding)
    - Training date
    - Usage count
    - Cost

- [ ] **Model Details View** - Modal or expanded view
  - Full training parameters
  - Training metrics (if available)
  - Usage history
  - Version history
  - Deploy/Delete buttons

---

## 🚀 Phase 4: Deploy-to-Node

### Embed Node Integration
- [ ] **Model Selector** - Dropdown in Embed node config
  - Option: "Use fine-tuned model"
  - Dropdown: List of available fine-tuned embedding models
  - Show model name, base model, training date

- [ ] **Model Loading** - Load fine-tuned model in Embed node
  - Use custom model ID instead of default
  - Handle model-specific parameters

- [ ] **Visual Indicator** - Show when using fine-tuned model
  - Badge on node: "Custom Model"
  - Tooltip: Model name and training date

### Chat Node Integration
- [ ] **Model Selector** - Dropdown in Chat node config
  - Option: "Use fine-tuned model"
  - Dropdown: List of available fine-tuned chat models
  - Filter by base model (gpt-3.5-turbo, gpt-4)

- [ ] **Model Loading** - Use fine-tuned model in Chat node
  - Pass custom model ID to OpenAI API
  - Track usage in Model Registry

- [ ] **Visual Indicator** - Show when using fine-tuned model
  - Badge on node: "Custom Model"
  - Different styling/color

### Deploy Button
- [ ] **Deploy from Registry** - Button in Model Registry panel
  - "Deploy to Embed" button (for embedding models)
  - "Deploy to Chat" button (for chat models)
  - Opens node config modal with model pre-selected

- [ ] **Quick Deploy** - Context menu on model card
  - Right-click → "Deploy to Embed"
  - Right-click → "Deploy to Chat"
  - Creates new node with model configured

---

## 📊 Phase 5: Usage Tracking & Analytics

### Usage Statistics
- [ ] **Track Usage** - Log when fine-tuned model is used
  - Record in Model Usage table
  - Track execution_id, node_type, timestamp

- [ ] **Usage Dashboard** - Show usage metrics
  - Total uses per model
  - Uses per day/week/month
  - Most popular models
  - Cost per use

### Performance Metrics
- [ ] **Model Performance** - Track model performance (if available)
  - Response time
  - Token usage
  - Error rate
  - User feedback (if implemented)

---

## 🎯 Implementation Priority

### MVP (Minimum Viable Product)
1. ✅ Fine-Tune Node (Core) - **DONE**
2. 🔄 Status Checking API - **IN PROGRESS**
3. 📦 Model Registry (Basic) - **NEXT**
4. 🚀 Deploy to Chat Node - **HIGH PRIORITY**

### Phase 2 (Enhanced Features)
5. Background polling & auto-resume
6. Visual progress display
7. Model versioning
8. Usage tracking

### Phase 3 (Advanced Features)
9. Deploy to Embed node
10. Performance analytics
11. Model comparison
12. A/B testing support

---

## 🔧 Technical Notes

### Async Job Handling
- Fine-tuning takes 30 mins - 2 hours
- Need to handle workflow pausing/resuming
- Options:
  1. **Polling**: Background service checks status every 5 min
  2. **Webhooks**: OpenAI webhooks (if available)
  3. **Manual Resume**: User clicks "Check Status" button

### Data Format
- OpenAI requires JSONL format
- Two formats supported:
  - Chat: `{"messages": [{"role": "user", "content": "..."}, ...]}`
  - Completion: `{"prompt": "...", "completion": "..."}`

### Cost Tracking
- Training cost: ~$0.008 per 1K tokens
- Usage cost: Varies by model
- Track both training and usage costs

---

## 📝 Next Steps

1. **Create Status API Endpoint** - Check fine-tuning job status
2. **Create Model Registry API** - Store and retrieve models
3. **Create Model Registry Frontend Panel** - Display models
4. **Update Chat Node** - Support fine-tuned models
5. **Add Deploy Button** - Quick deploy from registry

---

**Status:** Phase 1 Complete ✅ | Phase 2 In Progress 🔄

